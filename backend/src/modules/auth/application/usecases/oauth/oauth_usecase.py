import secrets

from src.modules.auth.domain.entities.user_account_entity import UserAccountEntity
from src.modules.auth.domain.entities.user_entity import UserEntity
from src.modules.auth.domain.events.auth_domain_events import UserCreatedEvent
from src.modules.auth.domain.events.auth_email_domain_events import EmailVerifiedEvent
from src.modules.auth.domain.services.user_account_domain_service import UserAccountDomainService
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.infrastructure.oauth.google_oauth_client import GoogleOAuthClient
from src.shared.exceptions.base_exceptions import (
    DomainError,
    InvalidError,
    NotFoundError,
    ServerError,
    UnAuthorizedError,
)
from src.shared.infrastructure.redis_client import get_redis
from src.shared.mediator.mediator import mediator


class OAuthLoginUseCase:
    def __init__(
        self,
        google_oauth_client: GoogleOAuthClient,
    ):
        self.clients = {"google": google_oauth_client}

    async def execute(self, provider: str) -> str:
        try:
            client = self.clients.get(provider)
            if client is None:
                raise InvalidError(error=f"Unsupported OAuth provider: {provider}")

            state = secrets.token_urlsafe(32)
            redis = await get_redis()
            await redis.setex(f"oauth_state:{state}", 300, provider)

            return client.get_authorization_url(state=state)

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to initiate OAuth login", internal_details=str(e)) from e


class OAuthCallbackUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_account_domain_service: UserAccountDomainService,
        google_oauth_client: GoogleOAuthClient,
    ):
        self.user_domain_service = user_domain_service
        self.user_account_domain_service = user_account_domain_service
        self.clients = {"google": google_oauth_client}

    async def execute(self, provider: str, code: str, state: str) -> UserEntity:
        try:
            client = self.clients.get(provider)
            if client is None:
                raise InvalidError(error=f"Unsupported OAuth provider: {provider}")

            redis = await get_redis()
            stored_state = await redis.get(f"oauth_state:{state}")
            if not stored_state:
                raise InvalidError(error="Invalid OAuth state")
            stored_provider = stored_state.decode() if isinstance(stored_state, bytes) else str(stored_state)
            if stored_provider not in {"pending", provider}:
                raise InvalidError(error="OAuth provider does not match the login request")
            await redis.delete(f"oauth_state:{state}")

            tokens = await client.exchange_code(code)
            access_token = tokens["access_token"]
            oauth_user = await client.get_user_info(access_token)

            existing_account = await self.user_account_domain_service.get_user_account_by_provider(
                provider=provider, provider_account_id=oauth_user.id
            )
            if existing_account:
                user = await self.user_domain_service.get_user_by_id(existing_account.user_id)
                if not user:
                    raise NotFoundError(error="User not found")
                if user.is_deleted():
                    raise UnAuthorizedError(error="Account is deactivated")
                if not user.is_active:
                    raise UnAuthorizedError(error="Account is deactivated")
                return user

            existing_user = await self.user_domain_service.get_user_by_email(oauth_user.email)
            if existing_user:
                if existing_user.has_active_deletion_schedule():
                    existing_user.cancel_scheduled_deletion()
                    await self.user_domain_service.update_user(existing_user)
                if not existing_user.is_active:
                    raise UnAuthorizedError(error="Account is deactivated")
                if not existing_user.is_email_verified():
                    existing_user.mark_email_verified()
                    await self.user_domain_service.update_user(existing_user)
                user = existing_user
            else:
                full_name = oauth_user.name or oauth_user.email.split("@")[0]
                user = UserEntity(
                    email=oauth_user.email,
                    full_name=full_name,
                )
                created = await self.user_domain_service.create_user(user)
                assert created.id is not None, "User ID must be set after creation"
                user = created

                user.mark_email_verified()
                await self.user_domain_service.update_user(user)

                user.add_event(
                    UserCreatedEvent(
                        user_id=user.id,
                        full_name=user.full_name,
                        email=user.email,
                    )
                )
                user.add_event(
                    EmailVerifiedEvent(
                        user_id=user.id,
                        email=user.email,
                        full_name=user.full_name,
                    )
                )
                for event in user.pull_events():
                    await mediator.publish(event)

            assert user.id is not None, "User ID must be set"
            account = UserAccountEntity(
                user_id=user.id,
                type=provider,
                provider=provider,
                provider_account_id=oauth_user.id,
            )
            await self.user_account_domain_service.create_user_account(account)

            return user

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="OAuth callback failed", internal_details=str(e)) from e

import json

from src.core.config.settings import config
from src.modules.email_account.domain.entities.email_account_entity import EmailAccountEntity
from src.modules.email_account.domain.entities.oauth_config_entity import OauthConfigEntity
from src.modules.email_account.domain.enums.email_account_enums import EmailAccountStatus
from src.modules.email_account.domain.events.email_account_domain_events import EmailAccountConnectedEvent
from src.modules.email_account.domain.services.email_account_domain_service import EmailAccountDomainService
from src.modules.email_account.infrastructure.oauth.google_mail_oauth_client import GoogleMailOAuthClient
from src.modules.email_account.application.usecases.test_connection_usecase import TestConnectionUseCase
from src.shared.exceptions.base_exceptions import ConflictError, DomainError, InvalidError, ServerError
from src.shared.infrastructure.encryption.fernet_encryption import encrypt
from src.shared.infrastructure.redis_client import get_redis
from src.shared.mediator.mediator import mediator


class OAuthCallbackUseCase:

    def __init__(
        self,
        email_account_domain_service: EmailAccountDomainService,
        google_mail_oauth_client: GoogleMailOAuthClient,
        test_connection_usecase: TestConnectionUseCase,
    ):
        self.email_account_domain_service = email_account_domain_service
        self.google_mail_oauth_client = google_mail_oauth_client
        self.test_connection_usecase = test_connection_usecase

    async def _reactivate_account(
        self, existing: EmailAccountEntity, refresh_token: str, provider: str, actor_id: int,
    ) -> dict:
        oauth_config = await self.email_account_domain_service.get_oauth_config(existing.oauth_config_id)
        if oauth_config and refresh_token:
            oauth_config.encrypted_refresh_token = encrypt(refresh_token)
            oauth_config.mark_updated()
            await self.email_account_domain_service.update_oauth_config(oauth_config)

        existing.mark_active()
        existing.updated_by_id = actor_id
        updated = await self.email_account_domain_service.update_account(existing)

        await self.test_connection_usecase.execute(
            account_uuid=updated.uuid,
            organization_id=updated.organization_id,
            actor_id=actor_id,
        )

        updated.add_event(
            EmailAccountConnectedEvent(
                account_id=updated.id,
                account_uuid=updated.uuid,
                organization_id=updated.organization_id,
                provider=provider,
                email=updated.email,
            )
        )
        for event in updated.pull_events():
            await mediator.publish(event)

        return {
            "uuid": updated.uuid,
            "email": updated.email,
            "provider": updated.provider,
            "status": updated.status,
        }

    async def _restore_soft_deleted_account(
        self, existing: EmailAccountEntity, refresh_token: str, provider: str, actor_id: int,
    ) -> dict:
        oauth_config = None
        if existing.oauth_config_id:
            oauth_config = await self.email_account_domain_service.get_oauth_config(existing.oauth_config_id)

        if oauth_config:
            if refresh_token:
                oauth_config.encrypted_refresh_token = encrypt(refresh_token)
                oauth_config.mark_updated()
                await self.email_account_domain_service.update_oauth_config(oauth_config)
        else:
            if not refresh_token:
                raise InvalidError(error="No refresh token returned by provider. Please re-authorize.")
            oauth_config = OauthConfigEntity(encrypted_refresh_token=encrypt(refresh_token))
            oauth_config = await self.email_account_domain_service.create_oauth_config(oauth_config)
            existing.oauth_config_id = oauth_config.id

        existing.deleted_at = None
        existing.mark_active()
        existing.updated_by_id = actor_id
        updated = await self.email_account_domain_service.update_account(existing)

        await self.test_connection_usecase.execute(
            account_uuid=updated.uuid,
            organization_id=updated.organization_id,
            actor_id=actor_id,
        )

        updated.add_event(
            EmailAccountConnectedEvent(
                account_id=updated.id,
                account_uuid=updated.uuid,
                organization_id=updated.organization_id,
                provider=provider,
                email=updated.email,
            )
        )
        for event in updated.pull_events():
            await mediator.publish(event)

        return {
            "uuid": updated.uuid,
            "email": updated.email,
            "provider": updated.provider,
            "status": updated.status,
        }

    async def execute(
        self,
        code: str,
        state: str,
    ) -> dict:
        try:
            redis = await get_redis()
            stored = await redis.get(f"email_oauth_state:{state}")
            if not stored:
                raise InvalidError(error="Invalid or expired OAuth state")
            await redis.delete(f"email_oauth_state:{state}")

            state_data = json.loads(stored)
            provider = state_data["provider"]
            organization_id = state_data["organization_id"]
            actor_id = state_data["actor_id"]
            stored_email = state_data.get("email")

            if provider != "gmail":
                raise InvalidError(error=f"Unsupported OAuth provider: {provider}")
            oauth_client = self.google_mail_oauth_client

            tokens = await oauth_client.exchange_code(code)
            user_info = await oauth_client.get_user_info(tokens["access_token"])
            refresh_token = tokens.get("refresh_token") or ""

            # If reconnecting, verify the same account is selected
            if stored_email and user_info.email != stored_email:
                raise InvalidError(error="You must reconnect the same email account")

            existing = await self.email_account_domain_service.get_by_email_and_organization(
                email=user_info.email, organization_id=organization_id,
            )

            # Reactivate existing reconnect_required account
            if existing and existing.status == EmailAccountStatus.RECONNECT_REQUIRED.value:
                return await self._reactivate_account(existing, refresh_token, provider, actor_id)

            # Active account with same email should not happen
            if existing:
                raise ConflictError(error="This email is already connected to your organization")

            deleted_existing = await self.email_account_domain_service.get_by_email_and_organization_including_deleted(
                email=user_info.email, organization_id=organization_id,
            )
            if deleted_existing and deleted_existing.deleted_at is not None:
                return await self._restore_soft_deleted_account(
                    deleted_existing, refresh_token, provider, actor_id
                )

            # New connection
            if not refresh_token:
                raise InvalidError(error="No refresh token returned by provider. Please re-authorize.")
            oauth_config = OauthConfigEntity(
                encrypted_refresh_token=encrypt(refresh_token),
            )
            created_oauth = await self.email_account_domain_service.create_oauth_config(oauth_config)

            entity = EmailAccountEntity(
                organization_id=organization_id,
                provider=provider,
                email=user_info.email,
                sender_name=user_info.name,
                status=EmailAccountStatus.ACTIVE.value,
                oauth_config_id=created_oauth.id,
                sending_limit=config.PROVIDER_DEFAULT_SENDING_LIMITS.get(provider, 100),
                created_by_id=actor_id,
            )
            created = await self.email_account_domain_service.create_account(entity)

            await self.test_connection_usecase.execute(
                account_uuid=created.uuid,
                organization_id=organization_id,
                actor_id=actor_id,
            )

            created.add_event(
                EmailAccountConnectedEvent(
                    account_id=created.id,
                    account_uuid=created.uuid,
                    organization_id=organization_id,
                    provider=provider,
                    email=created.email,
                )
            )
            for event in created.pull_events():
                await mediator.publish(event)

            return {
                "uuid": created.uuid,
                "email": created.email,
                "provider": created.provider,
                "status": created.status,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="OAuth callback failed", internal_details=str(e)) from e

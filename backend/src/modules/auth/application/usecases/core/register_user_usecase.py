from src.core.config.settings import config
from src.modules.auth.domain.entities.user_account_entity import UserAccountEntity
from src.modules.auth.domain.entities.user_entity import UserEntity
from src.modules.auth.domain.events.auth_domain_events import UserCreatedEvent
from src.modules.auth.domain.events.auth_email_domain_events import EmailVerificationTokenCreatedEvent
from src.modules.auth.domain.services.user_account_domain_service import UserAccountDomainService
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.modules.auth.domain.services.user_token_domain_service import UserTokenDomainService
from src.shared.exceptions.base_exceptions import ConflictError, DomainError, InvalidError, ServerError
from src.shared.infrastructure.background_task_manager.task_manager import task_manager
from src.shared.mediator.mediator import mediator


class RegisterUserUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_account_domain_service: UserAccountDomainService,
        user_session_domain_service: UserSessionDomainService,
        user_token_domain_service: UserTokenDomainService,
    ):
        self.user_domain_service = user_domain_service
        self.user_account_domain_service = user_account_domain_service
        self.user_session_domain_service = user_session_domain_service
        self.user_token_domain_service = user_token_domain_service

    async def execute(
        self,
        full_name: str,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        invite_token: str | None = None,
    ) -> dict:
        try:
            try:
                email = self.user_domain_service.validate_email(email)
            except InvalidError as e:
                raise InvalidError(error=e.error, errors={"email": e.error}) from e

            try:
                self.user_domain_service.validate_password(password)
            except InvalidError as e:
                raise InvalidError(error=e.error, errors={"password": e.error}) from e

            existing = await self.user_domain_service.get_user_by_email(email)
            if existing:
                raise ConflictError(
                    error="This email is already registered",
                    errors={"email": "This email is already registered"},
                )

            password_hash = self.user_domain_service.hash_password(password)

            user = UserEntity(full_name=full_name, email=email)
            new_user = await self.user_domain_service.create_user(user)

            assert new_user.id is not None, "User ID must be set after creation"

            account = UserAccountEntity(
                user_id=new_user.id,
                type="password",
                hashed_password=password_hash,
            )
            await self.user_account_domain_service.create_user_account(account)

            raw_token = await self.user_token_domain_service.create_user_token(
                user_id=new_user.id,
                type="email_verify",
                expiry_minutes=config.VERIFICATION_TOKEN_EXPIRE_HOURS * 60,
            )

            new_user.add_event(
                UserCreatedEvent(
                    user_id=new_user.id,
                    full_name=new_user.full_name,
                    email=new_user.email,
                )
            )
            new_user.add_event(
                EmailVerificationTokenCreatedEvent(
                    user_id=new_user.id,
                    email=new_user.email,
                    token=raw_token,
                    full_name=new_user.full_name,
                )
            )
            for event in new_user.pull_events():
                if isinstance(event, EmailVerificationTokenCreatedEvent):
                    # Email delivery must never block or fail the signup request.
                    # The verification email is sent in the background and its
                    # failure is logged, not returned to the caller.
                    task_manager.add_task(mediator.publish(event, raise_on_error=False))
                else:
                    await mediator.publish(event)

            return {
                "requires_login": True,
                "user": {
                    "uuid": new_user.uuid,
                    "full_name": new_user.full_name,
                    "email": new_user.email,
                    "theme": new_user.theme,
                    "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
                },
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="An error occurred while creating the user", internal_details=str(e)) from e

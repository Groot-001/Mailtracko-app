from src.modules.auth.domain.events.auth_password_domain_events import ForgotPasswordLinkCreatedEvent
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_token_domain_service import UserTokenDomainService
from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError
from src.shared.infrastructure.background_task_manager.task_manager import task_manager
from src.shared.mediator.mediator import mediator


class ForgotPasswordUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_token_domain_service: UserTokenDomainService,
    ):
        self.user_domain_service = user_domain_service
        self.user_token_domain_service = user_token_domain_service

    async def execute(self, email: str) -> dict:
        try:
            try:
                email = self.user_domain_service.validate_email(email)
            except InvalidError as e:
                raise InvalidError(error=e.error, errors={"email": e.error}) from e

            user = await self.user_domain_service.get_user_by_email(email)
            if not user or not user.id or not user.is_active:
                return {"message": "If the email exists, a reset link was sent"}

            await self.user_token_domain_service.invalidate_active_tokens(
                user_id=user.id, type="password_reset"
            )

            raw_token = await self.user_token_domain_service.create_user_token(
                user_id=user.id,
                type="password_reset",
                expiry_minutes=config.PASSWORD_RESET_TOKEN_EXPIRE_HOURS * 60,
            )

            user.add_event(
                ForgotPasswordLinkCreatedEvent(email=user.email, link=raw_token, full_name=user.full_name)
            )
            for event in user.pull_events():
                if isinstance(event, ForgotPasswordLinkCreatedEvent):
                    # Email delivery must never block or fail the forgot-password
                    # request. The reset email is sent in the background.
                    task_manager.add_task(mediator.publish(event, raise_on_error=False))
                else:
                    await mediator.publish(event)

            return {"message": "If the email exists, a reset link was sent"}
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to process forgot password", internal_details=str(e)) from e

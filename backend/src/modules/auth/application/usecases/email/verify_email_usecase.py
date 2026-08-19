from src.modules.auth.domain.events.auth_email_domain_events import (
    EmailVerificationTokenCreatedEvent,
    EmailVerifiedEvent,
)
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_token_domain_service import UserTokenDomainService
from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError
from src.shared.mediator.mediator import mediator


class VerifyEmailUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_token_domain_service: UserTokenDomainService,
    ):
        self.user_domain_service = user_domain_service
        self.user_token_domain_service = user_token_domain_service

    async def execute(self, user_id: int, token: str) -> None:
        try:
            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if not user:
                raise InvalidError(error="User not found")

            if user.is_email_verified():
                raise InvalidError(error="Email already verified")

            is_valid, user_token = await self.user_token_domain_service.verify_user_token(
                type="email_verify", token=token, user_id=user_id
            )
            if not is_valid or not user_token:
                raise InvalidError(error="Invalid or expired verification token")

            await self.user_token_domain_service.mark_token_as_used(user_token)
            await self.user_domain_service.mark_email_verified(user_id)

            user.add_event(EmailVerifiedEvent(user_id=user_id, email=user.email, full_name=user.full_name))
            for event in user.pull_events():
                await mediator.publish(event, raise_on_error=True)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to verify email", internal_details=str(e)) from e


class ResendVerificationUseCase:
    def __init__(
        self,
        user_domain_service: UserDomainService,
        user_token_domain_service: UserTokenDomainService,
    ):
        self.user_domain_service = user_domain_service
        self.user_token_domain_service = user_token_domain_service

    async def execute(self, user_id: int) -> None:
        try:
            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if not user:
                raise InvalidError(error="User not found")

            if user.is_email_verified():
                raise InvalidError(error="Email already verified")

            await self.user_token_domain_service.invalidate_active_tokens(
                user_id=user_id, type="email_verify"
            )

            raw_token = await self.user_token_domain_service.create_user_token(
                user_id=user_id,
                type="email_verify",
                expiry_minutes=config.VERIFICATION_TOKEN_EXPIRE_HOURS * 60,
            )

            user.add_event(
                EmailVerificationTokenCreatedEvent(
                    user_id=user_id, email=user.email, token=raw_token, full_name=user.full_name,
                )
            )
            for event in user.pull_events():
                await mediator.publish(event, raise_on_error=True)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to resend verification", internal_details=str(e)) from e

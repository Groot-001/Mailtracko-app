import json
import secrets

from src.modules.auth.domain.entities.user_account_entity import UserAccountEntity
from src.modules.auth.domain.events.auth_password_domain_events import PasswordChangedEvent
from src.modules.auth.domain.services.user_account_domain_service import UserAccountDomainService
from src.modules.auth.domain.services.user_domain_service import UserDomainService
from src.modules.auth.domain.services.user_session_domain_service import UserSessionDomainService
from src.modules.auth.domain.services.user_token_domain_service import UserTokenDomainService
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError
from src.shared.infrastructure.redis_client import get_redis
from src.shared.mediator.mediator import mediator


class VerifyForgotPasswordUseCase:
    """Two-step password reset: OTP verification followed by a short-lived reset challenge."""

    RESET_CHALLENGE_TTL_SECONDS = 600

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

    async def verify_code(self, token: str) -> dict:
        """Consume a valid password-reset OTP and issue a one-time reset challenge."""
        try:
            clean_token = token.strip()
            if not clean_token.isdigit() or len(clean_token) != 6:
                raise InvalidError(error="Verification code must be exactly 6 digits")

            is_valid, user_token = await self.user_token_domain_service.verify_user_token(
                type="password_reset", token=clean_token
            )
            if not is_valid or not user_token:
                raise InvalidError(error="Invalid or expired verification code")

            user = await self.user_domain_service.get_active_user_by_id(user_token.user_id)
            if not user:
                raise InvalidError(error="User not found")

            # The OTP is one-time. After this point only the opaque reset challenge
            # can authorize the password form.
            await self.user_token_domain_service.mark_token_as_used(user_token)

            reset_challenge = secrets.token_urlsafe(32)
            redis = await get_redis()
            await redis.setex(
                f"password_reset_challenge:{reset_challenge}",
                self.RESET_CHALLENGE_TTL_SECONDS,
                json.dumps({"user_id": user_token.user_id}),
            )
            return {
                "reset_challenge": reset_challenge,
                "expires_in": self.RESET_CHALLENGE_TTL_SECONDS,
            }
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to verify reset code", internal_details=str(e)) from e

    async def reset_with_challenge(self, reset_challenge: str, new_password: str) -> dict:
        """Reset the password only after a valid server-side reset challenge."""
        try:
            try:
                self.user_domain_service.validate_password(new_password)
            except InvalidError as e:
                raise InvalidError(error=e.error, errors={"new_password": e.error}) from e
            clean_challenge = reset_challenge.strip()
            if not clean_challenge:
                raise InvalidError(error="Invalid or expired reset challenge")

            redis = await get_redis()
            raw_payload = await redis.get(f"password_reset_challenge:{clean_challenge}")
            if not raw_payload:
                raise InvalidError(error="Invalid or expired reset challenge")
            if isinstance(raw_payload, bytes):
                raw_payload = raw_payload.decode()
            payload = json.loads(str(raw_payload))
            user_id = int(payload["user_id"])

            user = await self.user_domain_service.get_active_user_by_id(user_id)
            if not user:
                raise InvalidError(error="User not found")

            account = await self.user_account_domain_service.get_user_account_by_user_id(
                user_id=user_id, type="password"
            )
            new_hash = self.user_domain_service.hash_password(new_password)
            if account:
                account.update_password(new_hash)
                await self.user_account_domain_service.update_user_account(account)
            else:
                await self.user_account_domain_service.create_user_account(
                    UserAccountEntity(
                        user_id=user_id,
                        type="password",
                        hashed_password=new_hash,
                    )
                )

            await self.user_session_domain_service.revoke_all_sessions_for_user(user_id)
            user.add_event(PasswordChangedEvent(user_id=user_id))
            for event in user.pull_events():
                await mediator.publish(event)

            # Consume the challenge only after the reset succeeds. It cannot be replayed.
            await redis.delete(f"password_reset_challenge:{clean_challenge}")
            return {"message": "Password reset successfully"}
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to reset password", internal_details=str(e)) from e

    async def execute(self, token: str, new_password: str) -> dict:
        """Backward-compatible internal method routed through the secure two-step flow."""
        verified = await self.verify_code(token)
        return await self.reset_with_challenge(verified["reset_challenge"], new_password)

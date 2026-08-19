import pyotp

from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity
from src.modules.auth.domain.enums.user_activity_enums import UserActivityTypeEnum
from src.modules.auth.domain.repositories.user_activity_repository import IUserActivityRepository
from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.shared.exceptions.base_exceptions import DomainError, InvalidError, ServerError


class VerifyAndEnableTotpUseCase:
    def __init__(
        self,
        totp_repo: IUserTotpSecretRepository,
        user_activity_repo: IUserActivityRepository,
    ):
        self.totp_repo = totp_repo
        self.user_activity_repo = user_activity_repo

    async def execute(self, user_id: int, code: str) -> dict:
        try:
            totp_secret = await self.totp_repo.get_by(user_id=user_id)
            if not totp_secret:
                raise DomainError(error="2FA not initialized. Generate a setup first.")
            if totp_secret.enabled:
                raise DomainError(error="2FA is already enabled")

            totp = pyotp.TOTP(totp_secret.secret)
            if not totp.verify(code.strip(), valid_window=1):
                raise InvalidError(error="Invalid verification code")

            totp_secret.enabled = True
            totp_secret.mark_updated()
            await self.totp_repo.update(totp_secret)

            activity = UserActivityEntity(
                user_id=user_id,
                activity_type=UserActivityTypeEnum.TWO_FA_ENABLED.value,
                description="2FA enabled",
                metadata={},
            )
            await self.user_activity_repo.add(activity)

            return {"message": "2FA enabled successfully"}

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to enable 2FA", internal_details=str(e)) from e

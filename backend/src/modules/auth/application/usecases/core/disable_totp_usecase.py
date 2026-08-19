from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity
from src.modules.auth.domain.enums.user_activity_enums import UserActivityTypeEnum
from src.modules.auth.domain.repositories.user_activity_repository import IUserActivityRepository
from src.modules.auth.domain.repositories.user_totp_recovery_code_repository import (
    IUserTotpRecoveryCodeRepository,
)
from src.modules.auth.domain.repositories.user_totp_secret_repository import IUserTotpSecretRepository
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class DisableTotpUseCase:
    def __init__(
        self,
        totp_repo: IUserTotpSecretRepository,
        user_activity_repo: IUserActivityRepository,
        recovery_code_repo: IUserTotpRecoveryCodeRepository,
    ):
        self.totp_repo = totp_repo
        self.user_activity_repo = user_activity_repo
        self.recovery_code_repo = recovery_code_repo

    async def execute(self, user_id: int) -> dict:
        try:
            totp_secret = await self.totp_repo.get_by(user_id=user_id)
            if not totp_secret or not totp_secret.enabled:
                raise DomainError(error="2FA is not enabled")

            await self.totp_repo.delete(totp_secret.id)

            recovery_codes = await self.recovery_code_repo.filter(user_id=user_id)
            for rc in recovery_codes:
                await self.recovery_code_repo.delete(rc.id)

            activity = UserActivityEntity(
                user_id=user_id,
                activity_type=UserActivityTypeEnum.TWO_FA_DISABLED.value,
                description="2FA disabled",
                metadata={},
            )
            await self.user_activity_repo.add(activity)

            return {"message": "2FA disabled successfully"}

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(error="Failed to disable 2FA", internal_details=str(e)) from e

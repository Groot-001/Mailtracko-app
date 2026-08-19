from src.shared.domain.repository.base_repository_interface import IBaseRepository

from src.modules.auth.domain.entities.user_totp_recovery_code_entity import UserTotpRecoveryCodeEntity


class IUserTotpRecoveryCodeRepository(IBaseRepository[UserTotpRecoveryCodeEntity]):
    async def mark_used(self, entity_id: int) -> None:
        ...

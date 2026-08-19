from src.shared.domain.repository.base_repository_interface import IBaseRepository

from src.modules.auth.domain.entities.user_totp_secret_entity import UserTotpSecretEntity


class IUserTotpSecretRepository(IBaseRepository[UserTotpSecretEntity]):
    pass

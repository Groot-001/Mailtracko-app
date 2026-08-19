from src.shared.domain.repository.base_repository_interface import IBaseRepository

from src.modules.auth.domain.entities.user_token_entity import UserTokenEntity


class IUserTokenRepository(IBaseRepository[UserTokenEntity]):
    pass

from src.shared.domain.repository.base_repository_interface import IBaseRepository

from src.modules.auth.domain.entities.user_entity import UserEntity


class IUserRepository(IBaseRepository[UserEntity]):
    pass

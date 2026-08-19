from abc import ABC, abstractmethod

from src.modules.auth.domain.entities.user_activity_entity import UserActivityEntity


class IUserActivityRepository(ABC):
    @abstractmethod
    async def add(self, entity: UserActivityEntity) -> UserActivityEntity:
        pass

    @abstractmethod
    async def list_by_user(
        self, user_id: int, limit: int = 50, offset: int = 0,
    ) -> tuple[list[UserActivityEntity], int]:
        pass

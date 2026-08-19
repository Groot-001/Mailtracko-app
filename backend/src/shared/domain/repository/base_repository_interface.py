from abc import ABC, abstractmethod
from typing import TypeVar

from src.shared.domain.entity.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)


class IBaseRepository[TEntity](ABC):
    @abstractmethod
    async def add(self, entity: TEntity, *, audit: bool = True) -> TEntity: ...

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> TEntity | None: ...

    @abstractmethod
    async def get_by_uuid(self, entity_uuid: str) -> TEntity | None: ...

    @abstractmethod
    async def get_by(self, **criteria) -> TEntity | None: ...

    @abstractmethod
    async def update(self, entity: TEntity, *, audit: bool = True) -> TEntity: ...

    @abstractmethod
    async def delete(self, entity_id: int, audit: bool = True) -> None: ...

    @abstractmethod
    async def filter(self, **criteria) -> list[TEntity]: ...

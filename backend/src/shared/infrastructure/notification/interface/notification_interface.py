from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class INotification(ABC, Generic[T]):
    @abstractmethod
    async def send(self, message: T) -> Any:
        pass

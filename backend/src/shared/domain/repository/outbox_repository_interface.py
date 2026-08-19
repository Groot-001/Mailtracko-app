from abc import ABC, abstractmethod
from typing import Any


class IOutboxRepository(ABC):
    @abstractmethod
    async def add(self, event_type: str, payload: dict[str, Any]) -> None: ...

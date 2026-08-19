from abc import ABC, abstractmethod

from src.modules.contacts.domain.entities.contact_activity_entity import (
    ContactActivityEntity,
)


class IContactActivityRepository(ABC):
    """Repository interface for contact activity timeline."""

    @abstractmethod
    async def add(self, entity: ContactActivityEntity) -> ContactActivityEntity:
        """Log a new activity event."""
        pass

    @abstractmethod
    async def list_by_contact(
        self,
        contact_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactActivityEntity], int]:
        """Paginated timeline for a specific contact."""
        pass

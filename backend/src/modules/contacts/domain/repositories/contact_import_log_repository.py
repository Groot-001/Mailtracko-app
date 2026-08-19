from abc import ABC, abstractmethod

from src.modules.contacts.domain.entities.contact_import_log_entity import (
    ContactImportLogEntity,
)


class IContactImportLogRepository(ABC):
    """Repository interface for import job logs."""

    @abstractmethod
    async def add(self, entity: ContactImportLogEntity) -> ContactImportLogEntity:
        """Create a new import log entry."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> ContactImportLogEntity | None:
        """Get an import log by its primary key."""
        pass

    @abstractmethod
    async def get_by_uuid(self, uuid: str) -> ContactImportLogEntity | None:
        """Get an import log by its UUID."""
        pass

    @abstractmethod
    async def update(self, entity: ContactImportLogEntity) -> ContactImportLogEntity:
        """Update an import log (e.g. status change)."""
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactImportLogEntity], int]:
        """Paginated list of all import logs for an organization."""
        pass

    @abstractmethod
    async def list_by_list(
        self,
        contact_list_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactImportLogEntity], int]:
        """Paginated list of import logs for a specific list."""
        pass

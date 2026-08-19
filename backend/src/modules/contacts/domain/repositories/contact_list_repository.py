from src.shared.domain.repository.base_repository_interface import IBaseRepository

from src.modules.contacts.domain.entities.contact_list_entity import ContactListEntity


class IContactListRepository(IBaseRepository[ContactListEntity]):
    """Repository interface for contact list persistence."""

    async def list_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ContactListEntity], int]:
        """Paginated list of lists for an organization. Returns (items, total)."""
        ...

    async def list_summaries_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Return contact-list read models enriched with contact counters."""
        ...

    async def count_by_organization(self, organization_id: int) -> int:
        """Total number of lists in an organization."""
        ...

from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.shared.domain.repository.base_repository_interface import IBaseRepository


class IContactRepository(IBaseRepository[ContactEntity]):
    """Repository interface for contact persistence."""

    async def get_by_email_and_list(
        self,
        email: str,
        contact_list_id: int,
    ) -> ContactEntity | None:
        """Find a contact by email within a specific list (duplicate check)."""

    async def list_by_list(
        self,
        contact_list_id: int,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        subscribed: bool | None = None,
        company: str | None = None,
        tag: str | None = None,
        status: str | None = None,
        verification_status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[ContactEntity], int]:
        """Paginated, filterable, sortable list of contacts within a list."""

    async def count_by_list(self, contact_list_id: int) -> int:
        """Total number of contacts in a list."""

    async def bulk_upsert(
        self,
        entities: list[ContactEntity],
    ) -> tuple[list[ContactEntity], int]:
        """Bulk insert or update contacts within a list."""

    async def list_all_by_list(self, contact_list_id: int) -> list[ContactEntity]:
        """Fetch all contacts in a list (no pagination). Used for export."""

    async def get_existing_by_emails(
        self,
        emails: list[str],
        contact_list_id: int,
    ) -> list[ContactEntity]:
        """Return existing contacts matching the given emails within a list."""

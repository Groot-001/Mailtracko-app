from src.modules.contacts.domain.repositories.contact_activity_repository import (
    IContactActivityRepository,
)
from src.modules.contacts.domain.repositories.contact_repository import (
    IContactRepository,
)
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)


class ListContactTimelineUseCase:
    """Paginated timeline of activities for a specific contact."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
        contact_repo: IContactRepository,
        contact_activity_repo: IContactActivityRepository,
    ):
        self.contact_list_domain_service = contact_list_domain_service
        self.contact_repo = contact_repo
        self.contact_activity_repo = contact_activity_repo

    async def execute(
        self,
        list_uuid: str,
        contact_uuid: str,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        try:
            contact_list = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if contact_list.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )
            if contact_list.id is None:
                raise NotFoundError(error="Contact list not found")

            contact = await self.contact_repo.get_by_uuid(contact_uuid)
            if (
                not contact
                or contact.contact_list_id != contact_list.id
                or contact.id is None
            ):
                raise NotFoundError(error="Contact not found in this list")

            entities, total = await self.contact_activity_repo.list_by_contact(
                contact_id=contact.id,
                limit=limit,
                offset=offset,
            )

            items = [
                {
                    "uuid": e.uuid,
                    "activity_type": e.activity_type,
                    "description": e.description,
                    "metadata": e.metadata,
                    "created_at": e.created_at,
                }
                for e in entities
            ]

            return items, total

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while fetching contact timeline",
                internal_details=str(e),
            ) from e

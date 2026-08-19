from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListContactListsUseCase:
    """Use case for listing all contact lists in an organization (paginated)."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
    ):
        self.contact_list_domain_service = contact_list_domain_service

    async def execute(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        try:
            return await self.contact_list_domain_service.list_summaries_by_organization(
                organization_id,
                limit=limit,
                offset=offset,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while listing contact lists",
                internal_details=str(e),
            ) from e

from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)


class DeleteContactListUseCase:
    """Use case for soft-deleting a contact list."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
    ):
        self.contact_list_domain_service = contact_list_domain_service

    async def execute(
        self,
        list_uuid: str,
        organization_id: int,
    ) -> dict:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)

            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )

            await self.contact_list_domain_service.delete(list_uuid)

            return {
                "uuid": existing.uuid,
                "name": existing.name,
                "description": existing.description,
                "field_definitions": existing.field_definitions,
                "created_at": existing.created_at,
                "updated_at": existing.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while deleting contact list",
                internal_details=str(e),
            ) from e

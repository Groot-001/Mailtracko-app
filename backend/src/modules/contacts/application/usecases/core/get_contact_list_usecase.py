from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)


class GetContactListUseCase:
    """Use case for retrieving a single contact list by UUID."""

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
            entity = await self.contact_list_domain_service.get_by_uuid(list_uuid)

            if entity.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )

            return {
                "uuid": entity.uuid,
                "name": entity.name,
                "description": entity.description,
                "field_definitions": entity.field_definitions,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while retrieving contact list",
                internal_details=str(e),
            ) from e

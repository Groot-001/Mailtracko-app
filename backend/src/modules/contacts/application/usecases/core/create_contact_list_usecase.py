from src.modules.contacts.domain.entities.contact_list_entity import ContactListEntity
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.modules.contacts.presentation.schemas.contact_list_schemas import (
    CreateContactListRequestSchema,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class CreateContactListUseCase:
    """Use case for creating a new contact list within an organization."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
    ):
        self.contact_list_domain_service = contact_list_domain_service

    async def execute(
        self,
        payload: CreateContactListRequestSchema,
        actor_id: int,
        organization_id: int,
    ) -> dict:
        try:
            entity = ContactListEntity(
                organization_id=organization_id,
                name=payload.name,
                description=payload.description,
                created_by_id=actor_id,
            )

            created = await self.contact_list_domain_service.create(entity)

            return {
                "uuid": created.uuid,
                "name": created.name,
                "description": created.description,
                "field_definitions": created.field_definitions,
                "created_at": created.created_at,
                "updated_at": created.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while creating contact list",
                internal_details=str(e),
            ) from e

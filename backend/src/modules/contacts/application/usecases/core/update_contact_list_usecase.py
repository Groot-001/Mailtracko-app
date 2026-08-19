from src.modules.contacts.domain.entities.contact_list_entity import ContactListEntity
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.modules.contacts.presentation.schemas.contact_list_schemas import (
    UpdateContactListRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)


class UpdateContactListUseCase:
    """Use case for updating an existing contact list."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
    ):
        self.contact_list_domain_service = contact_list_domain_service

    async def execute(
        self,
        list_uuid: str,
        payload: UpdateContactListRequestSchema,
        actor_id: int,
        organization_id: int,
    ) -> dict:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)

            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )

            entity = ContactListEntity(
                id=existing.id,
                uuid=existing.uuid,
                organization_id=existing.organization_id,
                name=payload.name if payload.name is not None else existing.name,
                description=payload.description
                if payload.description is not None
                else existing.description,
                field_definitions=existing.field_definitions,
                created_at=existing.created_at,
                created_by_id=existing.created_by_id,
                updated_by_id=actor_id,
                deleted_at=existing.deleted_at,
            )

            updated = await self.contact_list_domain_service.update(
                list_uuid,
                entity,
                existing=existing,
            )

            return {
                "uuid": updated.uuid,
                "name": updated.name,
                "description": updated.description,
                "field_definitions": updated.field_definitions,
                "created_at": updated.created_at,
                "updated_at": updated.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while updating contact list",
                internal_details=str(e),
            ) from e

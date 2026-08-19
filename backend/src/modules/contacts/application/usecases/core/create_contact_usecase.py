from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.modules.contacts.domain.services.contact_domain_service import (
    ContactDomainService,
)
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.modules.contacts.presentation.schemas.contact_list_schemas import (
    CreateContactRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    NotFoundError,
    ServerError,
)


class CreateContactUseCase:
    """Use case for creating a new contact inside a contact list."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
        contact_domain_service: ContactDomainService,
    ):
        self.contact_list_domain_service = contact_list_domain_service
        self.contact_domain_service = contact_domain_service

    async def execute(
        self,
        list_uuid: str,
        payload: CreateContactRequestSchema,
        actor_id: int,
        organization_id: int,
    ) -> dict:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )
            if existing.id is None:
                raise NotFoundError(error="Contact list not found")

            entity = ContactEntity(
                organization_id=organization_id,
                contact_list_id=existing.id,
                email=payload.email,
                metadata=payload.metadata,
                subscribed=payload.subscribed,
            )

            created = await self.contact_domain_service.create(entity)

            return {
                "uuid": created.uuid,
                "email": created.email,
                "metadata": created.metadata,
                "subscribed": created.subscribed,
                "unsubscribed_at": created.unsubscribed_at,
                "last_contacted_at": created.last_contacted_at,
                "created_at": created.created_at,
                "updated_at": created.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while creating a contact",
                internal_details=str(e),
            ) from e

from src.modules.contacts.domain.repositories.contact_repository import (
    IContactRepository,
)
from src.modules.contacts.domain.services.contact_list_domain_service import (
    ContactListDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)


class DeleteContactUseCase:
    """Use case to delete a single contact by UUID within a list."""

    def __init__(
        self,
        contact_repo: IContactRepository,
        contact_list_domain_service: ContactListDomainService,
    ):
        self.contact_repo = contact_repo
        self.contact_list_domain_service = contact_list_domain_service

    async def execute(
        self, list_uuid: str, contact_uuid: str, organization_id: int
    ) -> dict:
        try:
            # validate list ownership / existence
            contact_list = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if contact_list.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )

            # find contact by uuid
            contact = await self.contact_repo.get_by_uuid(contact_uuid)
            if not contact:
                raise DomainError(error="Contact not found")

            if contact.contact_list_id != contact_list.id:
                raise ForbiddenError(
                    error="Contact does not belong to the specified list"
                )

            # delete (repository implements physical delete)
            await self.contact_repo.delete(contact.id)

            return {
                "uuid": contact.uuid,
                "email": contact.email,
                "metadata": contact.metadata,
                "subscribed": contact.subscribed,
                "unsubscribed_at": contact.unsubscribed_at,
                "last_contacted_at": contact.last_contacted_at,
                "created_at": contact.created_at,
                "updated_at": contact.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to delete contact", internal_details=str(e)
            ) from e

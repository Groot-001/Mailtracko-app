from src.modules.contacts.domain.entities.contact_entity import ContactEntity
from src.modules.contacts.domain.repositories.contact_repository import (
    IContactRepository,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    DomainError,
    ServerError,
)


class ContactDomainService:
    def __init__(self, repository: IContactRepository):
        self.repository = repository

    async def get_by_email_and_list(
        self, email: str, contact_list_id: int
    ) -> ContactEntity | None:
        try:
            return await self.repository.get_by_email_and_list(email, contact_list_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to look up contact by email", internal_details=str(e)
            ) from e

    async def get_existing_by_emails(
        self,
        emails: list[str],
        contact_list_id: int,
    ) -> list[ContactEntity]:
        """Return contacts matching the given emails within a list."""
        try:
            return await self.repository.get_existing_by_emails(emails, contact_list_id)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to look up existing contacts", internal_details=str(e)
            ) from e

    async def create(self, entity: ContactEntity) -> ContactEntity:
        try:
            existing = await self.repository.get_by_email_and_list(
                entity.email, entity.contact_list_id
            )
            if existing:
                raise ConflictError(
                    error="A contact with this email already exists in the list",
                    errors={"code": "CONTACT_EMAIL_ALREADY_EXISTS"},
                )
            return await self.repository.add(entity)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to create contact", internal_details=str(e)
            ) from e

    async def bulk_upsert(
        self, entities: list[ContactEntity]
    ) -> tuple[list[ContactEntity], int]:
        try:
            return await self.repository.bulk_upsert(entities)
        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to bulk upsert contacts", internal_details=str(e)
            ) from e

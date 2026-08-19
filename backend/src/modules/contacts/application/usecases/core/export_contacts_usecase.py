import csv
import io

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


FIELD_ORDER = [
    "email",
    "subscribed",
    "created_at",
    "updated_at",
    "last_contacted_at",
    "unsubscribed_at",
]


class ExportContactsUseCase:
    """Use case for exporting contacts as CSV."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
        contact_repo: IContactRepository,
    ):
        self.contact_list_domain_service = contact_list_domain_service
        self.contact_repo = contact_repo

    async def execute(self, list_uuid: str, organization_id: int) -> str:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )
            if existing.id is None:
                raise NotFoundError(error="Contact list not found")

            contacts = await self.contact_repo.list_all_by_list(existing.id)
            field_defs = existing.field_definitions or []

            headers = FIELD_ORDER + field_defs

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)

            for c in contacts:
                row = [
                    c.email,
                    str(c.subscribed).lower(),
                    c.created_at.isoformat() if c.created_at else "",
                    c.updated_at.isoformat() if c.updated_at else "",
                    c.last_contacted_at.isoformat() if c.last_contacted_at else "",
                    c.unsubscribed_at.isoformat() if c.unsubscribed_at else "",
                ]
                meta = c.metadata or {}
                row += [meta.get(fd, "") for fd in field_defs]
                writer.writerow(row)

            return output.getvalue()

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while exporting contacts",
                internal_details=str(e),
            ) from e

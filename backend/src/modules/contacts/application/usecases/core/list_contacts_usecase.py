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


class ListContactsUseCase:
    """Use case for listing contacts within a list with search, filter, and sort."""

    def __init__(
        self,
        contact_list_domain_service: ContactListDomainService,
        contact_repo: IContactRepository,
    ):
        self.contact_list_domain_service = contact_list_domain_service
        self.contact_repo = contact_repo

    async def execute(
        self,
        list_uuid: str,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        subscribed: bool | None = None,
        company: str | None = None,
        tag: str | None = None,
        status: str | None = None,
        verification_status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict], int]:
        try:
            existing = await self.contact_list_domain_service.get_by_uuid(list_uuid)
            if existing.organization_id != organization_id:
                raise ForbiddenError(
                    error="You do not have access to this contact list"
                )
            if existing.id is None:
                from src.shared.exceptions.base_exceptions import NotFoundError

                raise NotFoundError(error="Contact list not found")

            entities, total = await self.contact_repo.list_by_list(
                contact_list_id=existing.id,
                limit=limit,
                offset=offset,
                search=search,
                subscribed=subscribed,
                company=company,
                tag=tag,
                status=status,
                verification_status=verification_status,
                sort_by=sort_by,
                sort_order=sort_order,
            )

            items = [
                {
                    "uuid": e.uuid,
                    "email": e.email,
                    "metadata": e.metadata,
                    "subscribed": e.subscribed,
                    "unsubscribed_at": e.unsubscribed_at,
                    "last_contacted_at": e.last_contacted_at,
                    "status": e.status,
                    "verification_status": e.verification_status,
                    "verification_sub_status": e.verification_sub_status,
                    "verification_score": e.verification_score,
                    "verification_details": e.verification_details,
                    "verified_at": e.verified_at,
                    "bounce_risk": e.bounce_risk,
                    "last_bounced_at": e.last_bounced_at,
                    "archived_at": e.archived_at,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                }
                for e in entities
            ]

            return items, total

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while listing contacts",
                internal_details=str(e),
            ) from e

from src.modules.organization.domain.entities.organization_activity_entity import (
    OrganizationActivityEntity,
)
from src.modules.organization.domain.repositories.organization_activity_repository import (
    IOrganizationActivityRepository,
)
from src.shared.exceptions.base_exceptions import (
    CreateError,
    DomainError,
    ServerError,
)


class OrganizationActivityDomainService:
    """
    Service class for organization activity domain logic.
    """

    def __init__(
        self,
        repository: IOrganizationActivityRepository,
    ):
        self.repository = repository

    async def create_activity(
        self,
        activity_entity: OrganizationActivityEntity,
    ) -> OrganizationActivityEntity:
        """
        Creates organization activity.
        """
        try:
            return await self.repository.add(activity_entity)

        except DomainError:
            raise
        except Exception as e:
            raise CreateError(
                error="Failed to create organization activity",
                internal_details=str(e),
            ) from e

    async def list_recent_activities(
        self,
        organization_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> list[OrganizationActivityEntity]:
        """
        Lists recent organization activities.
        """
        try:
            return await self.repository.list_by_organization_id(
                organization_id=organization_id,
                limit=limit,
                offset=offset,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list organization activities",
                internal_details=str(e),
            ) from e

    async def count_recent_activities(
        self,
        organization_id: int,
    ) -> int:
        """
        Counts recent organization activities.
        """
        try:
            return await self.repository.count_by_organization_id(
                organization_id=organization_id,
            )

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to count organization activities",
                internal_details=str(e),
            ) from e
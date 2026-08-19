from src.modules.organization.domain.services.organization_activity_domain_service import (
    OrganizationActivityDomainService,
)
from src.shared.exceptions.base_exceptions import DomainError, ServerError


class ListRecentOrganizationActivitiesUseCase:
    """
    Usecase for listing recent organization activities.
    """

    def __init__(
        self,
        organization_activity_domain_service: OrganizationActivityDomainService,
    ):
        self.organization_activity_domain_service = organization_activity_domain_service

    async def execute(
        self,
        organization_id: int,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """
        Lists recent activities for current organization.
        """
        try:
            limit = self._normalize_limit(limit)
            offset = self._normalize_offset(offset)

            activities = (
                await self.organization_activity_domain_service.list_recent_activities(
                    organization_id=organization_id,
                    limit=limit,
                    offset=offset,
                )
            )

            total = await self.organization_activity_domain_service.count_recent_activities(
                organization_id=organization_id,
            )

            return {
                "items": [
                    {
                        "uuid": activity.uuid,
                        "activity_type": activity.activity_type,
                        "title": activity.title,
                        "actor_user_id": activity.actor_user_id,
                        "target_user_id": activity.target_user_id,
                        "target_email": activity.target_email,
                        "created_at": activity.created_at,
                    }
                    for activity in activities
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to list recent organization activities",
                internal_details=str(e),
            ) from e

    def _normalize_limit(self, limit: int) -> int:
        """
        Keeps activity list pagination safe for UI.
        """
        if limit < 1:
            return 10

        if limit > 50:
            return 50

        return limit

    def _normalize_offset(self, offset: int) -> int:
        """
        Keeps activity list offset safe for UI.
        """
        if offset < 0:
            return 0

        return offset
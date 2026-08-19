from src.core.config.settings import config
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationRoleCodeEnum,
)
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationDeletionRequestedEvent,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class RequestOrganizationDeletionUseCase:
    """
    Usecase for requesting/scheduling organization deletion.
    """

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
    ):
        self.organization_domain_service = organization_domain_service

    async def execute(
        self,
        organization_id: int,
        actor_id: int,
        actor_email: str,
        actor_role_code: str,
        actor_full_name: str,
    ) -> dict:
        """
        Schedules organization deletion if the current user is owner.

        If deletion is already scheduled, the existing scheduled deletion date
        is returned and the timer is not reset.
        """
        try:
            if actor_role_code != OrganizationRoleCodeEnum.OWNER.value:
                raise ForbiddenError(
                    error="Only organization owner can request organization deletion",
                    errors={
                        "code": "ONLY_OWNER_CAN_REQUEST_ORGANIZATION_DELETION",
                        "message": "Only organization owner can request organization deletion.",
                    },
                )

            existing_organization = (
                await self.organization_domain_service.get_organization_by_id(
                    organization_id=organization_id,
                )
            )

            if not existing_organization or existing_organization.id is None:
                raise ServerError(error="Organization not found")

            if existing_organization.scheduled_deletion_at is not None:
                return {
                    "uuid": existing_organization.uuid,
                    "name": existing_organization.name,
                    "deletion_requested_at": existing_organization.deletion_requested_at,
                    "deletion_requested_by_id": existing_organization.deletion_requested_by_id,
                    "scheduled_deletion_at": existing_organization.scheduled_deletion_at,
                    "message": "Organization deletion is already scheduled.",
                }

            organization = await self.organization_domain_service.request_organization_deletion(
                organization_id=organization_id,
                actor_id=actor_id,
                grace_period_days=config.ORGANIZATION_DELETION_GRACE_DAYS,
            )

            if organization.id is None or organization.scheduled_deletion_at is None:
                raise ServerError(
                    error="Failed to request organization deletion",
                    internal_details="Organization deletion schedule was not created",
                )

            organization.add_event(
                OrganizationDeletionRequestedEvent(
                    organization_id=organization.id,
                    organization_uuid=organization.uuid,
                    organization_name=organization.name,
                    owner_id=actor_id,
                    owner_email=actor_email,
                    owner_name=actor_full_name,
                    scheduled_deletion_at=organization.scheduled_deletion_at,
                )
            )

            for event in organization.pull_events():
                await mediator.publish(event)

            return {
                "uuid": organization.uuid,
                "name": organization.name,
                "deletion_requested_at": organization.deletion_requested_at,
                "deletion_requested_by_id": organization.deletion_requested_by_id,
                "scheduled_deletion_at": organization.scheduled_deletion_at,
                "message": "Organization deletion has been scheduled successfully.",
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to request organization deletion",
                internal_details=str(e),
            ) from e
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationMemberRemovedEvent,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.shared.exceptions.base_exceptions import (
    DomainError,
    ForbiddenError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class RemoveOrganizationMemberUseCase:
    """
    Use case for removing a member from the organization.
    """

    def __init__(
        self,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(
        self,
        member_id: int,
        organization_id: int,
        actor_id: int,
        actor_role_code: str,
    ) -> dict:
        """
        Removes a member from the organization.
        """
        try:
            self._ensure_actor_can_remove_members(actor_role_code)

            removed_member = await self.organization_member_domain_service.remove_member(
                member_id=member_id,
                organization_id=organization_id,
                actor_id=actor_id,
                actor_role_code=actor_role_code,
            )

            if removed_member.id is None:
                raise ServerError(
                    error="Failed to remove organization member",
                    internal_details="Removed member id is missing",
                )

            removed_member_id = removed_member.id

            removed_member.add_event(
                OrganizationMemberRemovedEvent(
                    member_id=removed_member_id,
                    user_id=removed_member.user_id,
                    organization_id=organization_id,
                    removed_by_id=actor_id,
                )
            )

            for event in removed_member.pull_events():
                await mediator.publish(event)

            return {
                "uuid": removed_member.uuid,
                "user_id": removed_member.user_id,
                "role_code": removed_member.role_code,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while removing organization member",
                internal_details=str(e),
            ) from e

    def _ensure_actor_can_remove_members(
        self,
        actor_role_code: str,
    ) -> None:
        """
        Ensures only owner or admin can remove members.
        """
        from src.modules.organization.domain.enums.organization_enums import (
            OrganizationRoleCodeEnum,
        )

        if actor_role_code not in {
            OrganizationRoleCodeEnum.OWNER.value,
            OrganizationRoleCodeEnum.ADMIN.value,
        }:
            raise ForbiddenError(
                error="Only organization owner or admin can remove members",
                errors={
                    "code": "ONLY_MANAGER_CAN_REMOVE",
                    "message": "Only organization owner or admin can remove members.",
                },
            )
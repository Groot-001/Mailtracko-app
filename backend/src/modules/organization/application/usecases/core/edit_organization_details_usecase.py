from src.modules.organization.domain.entities.organization_entity import (
    OrganizationEntity,
)
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationUpdatedEvent,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.modules.organization.presentation.schemas.organization_schemas import (
    EditOrganizationRequestSchema,
)
from src.shared.exceptions.base_exceptions import DomainError, ForbiddenError, ServerError
from src.shared.mediator.mediator import mediator


class EditOrganizationDetailsUseCase:
    """
    Use case for editing organization details.
    """

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_domain_service = organization_domain_service
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(
        self,
        organization_uuid: str,
        payload: EditOrganizationRequestSchema,
        actor_id: int,
    ) -> OrganizationEntity:
        """
        Applies organization changes and returns updated organization.
        """
        try:
            organization = (
                await self.organization_domain_service.get_organization_by_uuid(
                    organization_uuid
                )
            )

            if not organization or organization.id is None:
                raise ServerError(
                    error="Error while retrieving organization details",
                    internal_details=f"No organization found with uuid {organization_uuid}",
                )

            organization_id = organization.id

            await self._ensure_actor_can_edit_organization(
                organization_id=organization_id,
                actor_id=actor_id,
            )

            fields = payload.model_dump(exclude_unset=True)

            updated_organization = await self._apply_organization_changes(
                organization=organization,
                fields=fields,
                actor_id=actor_id,
            )

            if updated_organization.id is None:
                raise ServerError(
                    error="Failed to edit organization details",
                    internal_details="Updated organization ID is missing",
                )

            updated_organization.add_event(
                OrganizationUpdatedEvent(
                    organization_id=updated_organization.id,
                    organization_uuid=updated_organization.uuid,
                    updated_by_id=actor_id,
                )
            )

            for event in updated_organization.pull_events():
                await mediator.publish(event)

            return updated_organization

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="Failed to edit organization details",
                internal_details=str(e),
            ) from e

    async def _apply_organization_changes(
        self,
        organization: OrganizationEntity,
        fields: dict,
        actor_id: int,
    ) -> OrganizationEntity:
        """
        Updates allowed organization fields.
        """
        if not fields:
            return organization

        for key, value in fields.items():
            if hasattr(value, "value"):
                value = value.value

            setattr(organization, key, value)

        return await self.organization_domain_service.update_organization(
            organization,
            actor_id,
        )

    async def _ensure_actor_can_edit_organization(
        self,
        *,
        organization_id: int,
        actor_id: int,
    ) -> None:
        """
        Ensures only organization owner can edit organization details.
        """
        member = (
            await self.organization_member_domain_service.get_member_by_user_and_organization(
                organization_id=organization_id,
                user_id=actor_id,
            )
        )

        if not member or not member.can_edit_organization():
            raise ForbiddenError(
                error="Only organization owner can edit organization details",
                errors={
                    "code": "ONLY_OWNER_CAN_EDIT",
                    "message": "Only organization owner can edit organization details.",
                },
            )
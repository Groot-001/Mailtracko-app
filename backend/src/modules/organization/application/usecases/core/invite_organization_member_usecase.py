from datetime import UTC, datetime, timedelta

from src.modules.organization.domain.entities.organization_invitation_entity import (
    OrganizationInvitationEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationInvitationStatusEnum,
)
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationInvitationCreatedEvent,
)
from src.modules.organization.domain.services.organization_domain_service import (
    OrganizationDomainService,
)
from src.modules.organization.domain.services.organization_invitation_domain_service import (
    OrganizationInvitationDomainService,
)
from src.modules.organization.domain.services.organization_member_domain_service import (
    OrganizationMemberDomainService,
)
from src.modules.organization.presentation.schemas.organization_schemas import (
    InviteOrganizationMemberRequestSchema,
)
from src.shared.exceptions.base_exceptions import (
    ConflictError,
    CreateError,
    DomainError,
    ForbiddenError,
    ServerError,
)
from src.shared.mediator.mediator import mediator


class InviteOrganizationMemberUseCase:
    """
    Use case for inviting user to organization.
    """

    def __init__(
        self,
        organization_domain_service: OrganizationDomainService,
        organization_invitation_domain_service: OrganizationInvitationDomainService,
        organization_member_domain_service: OrganizationMemberDomainService,
    ):
        self.organization_domain_service = organization_domain_service
        self.organization_invitation_domain_service = (
            organization_invitation_domain_service
        )
        self.organization_member_domain_service = organization_member_domain_service

    async def execute(
        self,
        organization_id: int,
        payload: InviteOrganizationMemberRequestSchema,
        actor_id: int,
    ) -> dict:
        """
        Creates an invitation for the given email.

        Owner/admin invites user through email. User becomes member only after accepting.
        """
        try:
            organization = await self.organization_domain_service.get_organization_by_id(
                organization_id=organization_id,
            )

            if not organization or organization.id is None:
                raise ServerError(error="Organization not found")

            current_organization_id = organization.id

            await self._ensure_actor_can_invite(
                organization_id=current_organization_id,
                actor_id=actor_id,
            )

            role_code = self._get_value(payload.role_code)
            invitee_email = str(payload.email).strip().lower()

            # Backend-authoritative duplicate protection: a member and a pending
            # invitation are distinct cases and must never report false success.
            existing_members, _ = await self.organization_member_domain_service.list_paginated_with_users(
                organization_id=current_organization_id,
                search=invitee_email,
                limit=10,
                offset=0,
            )
            if any(
                str((item.get("user") or {}).get("email") or "").strip().lower() == invitee_email
                for item in existing_members
            ):
                raise ConflictError(error="User already exists in this organization")

            pending_invitation = await self.organization_invitation_domain_service.get_pending_invitation_by_email(
                organization_id=current_organization_id,
                email=invitee_email,
            )
            if pending_invitation:
                raise ConflictError(error="An invitation for this user is already pending")

            invitation_token = (
                self.organization_invitation_domain_service.generate_invitation_token()
            )
            token_hash = (
                self.organization_invitation_domain_service.hash_invitation_token(
                    invitation_token
                )
            )

            invitation = OrganizationInvitationEntity(
                organization_id=current_organization_id,
                email=invitee_email,
                role_code=role_code,
                token_hash=token_hash,
                status=OrganizationInvitationStatusEnum.PENDING.value,
                invited_by_id=actor_id,
                expires_at=datetime.now(UTC) + timedelta(days=7),
                created_by_id=actor_id,
            )

            created_invitation = (
                await self.organization_invitation_domain_service.create_invitation(
                    invitation
                )
            )

            if created_invitation.id is None:
                raise CreateError(error="Failed to create organization invitation")

            created_invitation_id = created_invitation.id

            created_invitation.add_event(
                OrganizationInvitationCreatedEvent(
                    invitation_id=created_invitation_id,
                    organization_id=current_organization_id,
                    organization_name=organization.name,
                    inviter_id=actor_id,
                    invitee_email=invitee_email,
                    token=invitation_token,
                )
            )

            for event in created_invitation.pull_events():
                await mediator.publish(event, raise_on_error=True)

            return {
                "uuid": created_invitation.uuid,
                "email": created_invitation.email,
                "role_code": created_invitation.role_code,
                "status": created_invitation.status,
                "expires_at": created_invitation.expires_at,
                "created_at": created_invitation.created_at,
                "updated_at": created_invitation.updated_at,
            }

        except DomainError:
            raise
        except Exception as e:
            raise ServerError(
                error="An error occurred while creating organization invitation",
                internal_details=str(e),
            ) from e

    async def _ensure_actor_can_invite(
        self,
        *,
        organization_id: int,
        actor_id: int,
    ) -> None:
        """
        Ensures only organization owner or admin can invite users.
        """
        member = (
            await self.organization_member_domain_service.get_member_by_user_and_organization(
                organization_id=organization_id,
                user_id=actor_id,
            )
        )

        if not member or not member.can_manage_members():
            raise ForbiddenError(
                error="Only organization owner or admin can invite users",
                errors={
                    "code": "ONLY_MANAGER_CAN_INVITE",
                    "message": "Only organization owner or admin can invite users.",
                },
            )

    def _get_value(self, value):
        """
        Returns enum value when enum is passed, otherwise returns plain value.
        """
        return value.value if hasattr(value, "value") else value

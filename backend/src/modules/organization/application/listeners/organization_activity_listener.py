from src.modules.organization.domain.entities.organization_activity_entity import (
    OrganizationActivityEntity,
)
from src.modules.organization.domain.enums.organization_enums import (
    OrganizationActivityTypeEnum,
    OrganizationRoleCodeEnum,
)
from src.modules.organization.domain.events.organization_domain_events import (
    OrganizationCreatedEvent,
    OrganizationDeletionRequestedEvent,
    OrganizationInvitationAcceptedEvent,
    OrganizationInvitationCreatedEvent,
    OrganizationInvitationDeclinedEvent,
    OrganizationInvitationRevokedEvent,
    OrganizationMemberAddedEvent,
    OrganizationMemberRemovedEvent,
    OrganizationUpdatedEvent,
)
from src.modules.organization.domain.services.organization_activity_domain_service import (
    OrganizationActivityDomainService,
)
from src.modules.organization.infrastructure.repositories.organization_activity_repository_impl import (
    OrganizationActivityRepositoryImpl,
)
from src.modules.organization.infrastructure.uow.organization_uow import OrganizationUOW
from src.shared.infrastructure.db import get_async_session
from src.shared.infrastructure.logger import logger
from src.shared.mediator.listener import listener


async def _create_organization_activity(
    *,
    organization_id: int,
    activity_type: str,
    title: str,
    actor_user_id: int | None = None,
    target_user_id: int | None = None,
    target_email: str | None = None,
) -> None:
    """
    Creates a recent organization activity record.
    """
    try:
        async for session in get_async_session():
            async with OrganizationUOW(session):
                repository = OrganizationActivityRepositoryImpl(session=session)
                domain_service = OrganizationActivityDomainService(
                    repository=repository,
                )

                activity = OrganizationActivityEntity(
                    organization_id=organization_id,
                    activity_type=activity_type,
                    title=title,
                    actor_user_id=actor_user_id,
                    target_user_id=target_user_id,
                    target_email=target_email,
                    created_by_id=actor_user_id,
                    updated_by_id=actor_user_id,
                )

                await domain_service.create_activity(activity)

            break

    except Exception:
        logger.exception(
            "Failed to create organization activity: organization_id=%s activity_type=%s",
            organization_id,
            activity_type,
        )


@listener(OrganizationCreatedEvent)
async def on_organization_created_activity(event: OrganizationCreatedEvent):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.ORGANIZATION_CREATED.value,
        title="Organization was created",
        actor_user_id=event.owner_id,
        target_user_id=event.owner_id,
    )


@listener(OrganizationUpdatedEvent)
async def on_organization_updated_activity(event: OrganizationUpdatedEvent):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.ORGANIZATION_UPDATED.value,
        title="Organization details were updated",
        actor_user_id=event.updated_by_id,
    )


@listener(OrganizationDeletionRequestedEvent)
async def on_organization_deletion_requested_activity(
    event: OrganizationDeletionRequestedEvent,
):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.ORGANIZATION_DELETION_REQUESTED.value,
        title="Organization deletion was requested",
        actor_user_id=event.owner_id,
        target_user_id=event.owner_id,
    )


@listener(OrganizationMemberAddedEvent)
async def on_organization_member_added_activity(event: OrganizationMemberAddedEvent):
    if event.role_code == OrganizationRoleCodeEnum.OWNER.value:
        return

    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.MEMBER_ADDED.value,
        title="A member was added to the organization",
        actor_user_id=None,
        target_user_id=event.user_id,
    )


@listener(OrganizationMemberRemovedEvent)
async def on_organization_member_removed_activity(
    event: OrganizationMemberRemovedEvent,
):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.MEMBER_REMOVED.value,
        title="A member was removed from the organization",
        actor_user_id=event.removed_by_id,
        target_user_id=event.user_id,
    )


@listener(OrganizationInvitationCreatedEvent)
async def on_organization_invitation_created_activity(
    event: OrganizationInvitationCreatedEvent,
):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.INVITATION_SENT.value,
        title=f"Invitation sent to {event.invitee_email}",
        actor_user_id=event.inviter_id,
        target_email=event.invitee_email,
    )


@listener(OrganizationInvitationAcceptedEvent)
async def on_organization_invitation_accepted_activity(
    event: OrganizationInvitationAcceptedEvent,
):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.INVITATION_ACCEPTED.value,
        title=f"{event.invitee_email} accepted the invitation",
        actor_user_id=event.user_id,
        target_user_id=event.user_id,
        target_email=event.invitee_email,
    )


@listener(OrganizationInvitationDeclinedEvent)
async def on_organization_invitation_declined_activity(
    event: OrganizationInvitationDeclinedEvent,
):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.INVITATION_DECLINED.value,
        title=f"{event.invitee_email} declined the invitation",
        actor_user_id=event.actor_user_id,
        target_email=event.invitee_email,
    )


@listener(OrganizationInvitationRevokedEvent)
async def on_organization_invitation_revoked_activity(
    event: OrganizationInvitationRevokedEvent,
):
    await _create_organization_activity(
        organization_id=event.organization_id,
        activity_type=OrganizationActivityTypeEnum.INVITATION_REVOKED.value,
        title=f"Invitation to {event.invitee_email} was revoked",
        actor_user_id=event.revoked_by_id,
        target_email=event.invitee_email,
    )
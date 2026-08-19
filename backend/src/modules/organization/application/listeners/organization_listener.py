from src.core.config.settings import config
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
from src.shared.infrastructure.logger import logger
from src.shared.infrastructure.notification.adapter.email.email_notification import (
    EmailMessageData,
    EmailNotification,
)
from src.shared.mediator.listener import listener

email_notification = EmailNotification()


@listener(OrganizationCreatedEvent)
async def on_organization_created(event: OrganizationCreatedEvent):
    logger.info(
        "[OrgListener] Organization created: org_id=%s name=%s owner_id=%s",
        event.organization_id,
        event.name,
        event.owner_id,
    )


@listener(OrganizationUpdatedEvent)
async def on_organization_updated(event: OrganizationUpdatedEvent):
    logger.info(
        "[OrgListener] Organization updated: org_id=%s updated_by=%s",
        event.organization_id,
        event.updated_by_id,
    )


@listener(OrganizationDeletionRequestedEvent)
async def on_organization_deletion_requested(
    event: OrganizationDeletionRequestedEvent,
):
    logger.info(
        "[OrgListener] Organization deletion requested: org_id=%s owner_id=%s scheduled_deletion_at=%s",
        event.organization_id,
        event.owner_id,
        event.scheduled_deletion_at,
    )

    message = EmailMessageData(
        subject=f"{event.organization_name} is scheduled for deletion",
        template_name="organization/deletion_requested.html",
        context={
            "organization_name": event.organization_name,
            "owner_name": event.owner_name,
            "scheduled_deletion_at": event.scheduled_deletion_at,
        },
        recipient=[event.owner_email],
    )

    try:
        await email_notification.send(message)
    except Exception:
        logger.exception(
            "Failed to send organization deletion email to %s",
            event.owner_email,
        )


@listener(OrganizationMemberAddedEvent)
async def on_organization_member_added(event: OrganizationMemberAddedEvent):
    logger.info(
        "[OrgListener] Member added: member_id=%s user_id=%s org_id=%s role=%s",
        event.member_id,
        event.user_id,
        event.organization_id,
        event.role_code,
    )


@listener(OrganizationMemberRemovedEvent)
async def on_organization_member_removed(event: OrganizationMemberRemovedEvent):
    logger.info(
        "[OrgListener] Member removed: member_id=%s user_id=%s org_id=%s",
        event.member_id,
        event.user_id,
        event.organization_id,
    )


@listener(OrganizationInvitationCreatedEvent)
async def on_organization_invitation_created(event: OrganizationInvitationCreatedEvent):
    logger.info(
        "[OrgListener] Invitation created: invitation_id=%s org_id=%s email=%s",
        event.invitation_id,
        event.organization_id,
        event.invitee_email,
    )

    invitation_link = f"{config.FRONTEND_URL}/invite?token={event.token}"
    decline_link = f"{config.FRONTEND_URL}/invite/decline?token={event.token}"

    message = EmailMessageData(
        subject=f"You're invited to join {event.organization_name}",
        template_name="organization/invitation.html",
        context={
            "organization_name": event.organization_name,
            "invitee_name": event.invitee_name,
            "invitation_link": invitation_link,
            "decline_link": decline_link,
        },
        recipient=[event.invitee_email],
    )

    try:
        await email_notification.send(message)
    except Exception:
        logger.exception(
            "Failed to send invitation email to %s",
            event.invitee_email,
        )
        # Invitations are user-triggered transactional mail. Surface a final
        # delivery failure so the API does not report a misleading success.
        raise


@listener(OrganizationInvitationAcceptedEvent)
async def on_organization_invitation_accepted(
    event: OrganizationInvitationAcceptedEvent,
):
    logger.info(
        "[OrgListener] Invitation accepted: invitation_id=%s org_id=%s user_id=%s",
        event.invitation_id,
        event.organization_id,
        event.user_id,
    )


@listener(OrganizationInvitationDeclinedEvent)
async def on_organization_invitation_declined(
    event: OrganizationInvitationDeclinedEvent,
):
    logger.info(
        "[OrgListener] Invitation declined: invitation_id=%s org_id=%s",
        event.invitation_id,
        event.organization_id,
    )


@listener(OrganizationInvitationRevokedEvent)
async def on_organization_invitation_revoked(
    event: OrganizationInvitationRevokedEvent,
):
    logger.info(
        "[OrgListener] Invitation revoked: invitation_id=%s org_id=%s revoked_by=%s",
        event.invitation_id,
        event.organization_id,
        event.revoked_by_id,
    )
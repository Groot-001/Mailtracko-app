from dataclasses import dataclass
from datetime import datetime

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class OrganizationCreatedEvent(DomainEvent):
    organization_id: int
    organization_uuid: str
    name: str
    owner_id: int


@dataclass(kw_only=True, frozen=True)
class OrganizationUpdatedEvent(DomainEvent):
    organization_id: int
    organization_uuid: str
    updated_by_id: int


@dataclass(kw_only=True, frozen=True)
class OrganizationDeletionRequestedEvent(DomainEvent):
    organization_id: int
    organization_uuid: str
    organization_name: str
    owner_id: int
    owner_email: str
    owner_name: str
    scheduled_deletion_at: datetime


@dataclass(kw_only=True, frozen=True)
class OrganizationMemberAddedEvent(DomainEvent):
    member_id: int
    user_id: int
    organization_id: int
    role_code: str


@dataclass(kw_only=True, frozen=True)
class OrganizationMemberRemovedEvent(DomainEvent):
    member_id: int
    user_id: int
    organization_id: int
    removed_by_id: int


@dataclass(kw_only=True, frozen=True)
class OrganizationInvitationCreatedEvent(DomainEvent):
    invitation_id: int
    organization_id: int
    organization_name: str
    inviter_id: int
    invitee_email: str
    token: str
    invitee_name: str | None = None


@dataclass(kw_only=True, frozen=True)
class OrganizationInvitationAcceptedEvent(DomainEvent):
    invitation_id: int
    organization_id: int
    user_id: int
    invitee_email: str

@dataclass(kw_only=True, frozen=True)
class OrganizationInvitationDeclinedEvent(DomainEvent):
    invitation_id: int
    organization_id: int
    invitee_email: str
    actor_user_id: int | None = None

@dataclass(kw_only=True, frozen=True)
class OrganizationInvitationRevokedEvent(DomainEvent):
    invitation_id: int
    organization_id: int
    revoked_by_id: int
    invitee_email: str

@dataclass(kw_only=True, frozen=True)
class OrganizationDeletedEvent(DomainEvent):
    organization_id: int
    organization_uuid: str
    organization_name: str
    deleted_user_ids: list[int]
    deleted_by_id: int | None = None
    deleted_at: datetime
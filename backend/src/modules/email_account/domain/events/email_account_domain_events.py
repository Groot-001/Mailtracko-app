from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class EmailAccountConnectedEvent(DomainEvent):
    account_id: int
    account_uuid: str
    organization_id: int
    provider: str
    email: str


@dataclass(kw_only=True, frozen=True)
class EmailAccountVerifiedEvent(DomainEvent):
    account_id: int
    account_uuid: str
    organization_id: int
    email: str


@dataclass(kw_only=True, frozen=True)
class EmailAccountDisconnectedEvent(DomainEvent):
    account_id: int
    account_uuid: str
    organization_id: int
    email: str


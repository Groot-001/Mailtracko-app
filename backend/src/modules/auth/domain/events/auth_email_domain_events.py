from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class EmailVerificationTokenCreatedEvent(DomainEvent):
    user_id: int
    email: str
    token: str
    full_name: str


@dataclass(kw_only=True, frozen=True)
class EmailVerifiedEvent(DomainEvent):
    user_id: int
    email: str
    full_name: str


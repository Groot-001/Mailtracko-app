from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class UserCreatedEvent(DomainEvent):
    user_id: int
    full_name: str
    email: str


@dataclass(kw_only=True, frozen=True)
class UserUpdatedEvent(DomainEvent):
    user_id: int
    prev_value: str | None = None
    value: str | None = None


@dataclass(kw_only=True, frozen=True)
class AccountDeletedEvent(DomainEvent):
    user_id: int

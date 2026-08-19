from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class UserSessionUpdatedEvent(DomainEvent):
    session_uuid: str
    prev_value: str | None = None
    value: str | None = None

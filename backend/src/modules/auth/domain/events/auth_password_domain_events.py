from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class ForgotPasswordLinkCreatedEvent(DomainEvent):
    email: str
    link: str
    full_name: str


@dataclass(kw_only=True, frozen=True)
class PasswordChangedEvent(DomainEvent):
    user_id: int

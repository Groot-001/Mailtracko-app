from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class ContactImportedEvent(DomainEvent):
    """Published when a CSV/Sheets import job completes."""

    organization_id: int
    import_log_id: int
    contact_list_id: int
    total_imported: int
    total_errors: int
    filename: str


@dataclass(kw_only=True, frozen=True)
class ContactUnsubscribedEvent(DomainEvent):
    """Published when a contact is unsubscribed by the campaign module."""

    contact_id: int
    contact_uuid: str
    organization_id: int
    email: str

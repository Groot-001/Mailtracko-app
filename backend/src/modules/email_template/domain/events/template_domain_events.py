from dataclasses import dataclass

from src.shared.domain.events.base_domain_events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class TemplateCreatedEvent(DomainEvent):
    template_id: int
    template_uuid: str
    organization_id: int
    created_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplateUpdatedEvent(DomainEvent):
    template_id: int
    template_uuid: str
    organization_id: int
    updated_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplatePublishedEvent(DomainEvent):
    template_id: int
    template_uuid: str
    organization_id: int
    published_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplateArchivedEvent(DomainEvent):
    template_id: int
    template_uuid: str
    organization_id: int
    archived_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplateDuplicatedEvent(DomainEvent):
    template_id: int
    template_uuid: str
    source_template_id: int
    organization_id: int
    duplicated_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplateDeletedEvent(DomainEvent):
    template_id: int
    template_uuid: str
    organization_id: int
    deleted_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplateRestoredEvent(DomainEvent):
    template_id: int
    template_uuid: str
    organization_id: int
    restored_by_id: int
    
@dataclass(kw_only=True, frozen=True)
class TemplateAssetCreatedEvent(DomainEvent):
    asset_id: int
    asset_uuid: str
    template_id: int
    organization_id: int
    uploaded_by_id: int


@dataclass(kw_only=True, frozen=True)
class TemplateAssetDeletedEvent(DomainEvent):
    asset_id: int
    asset_uuid: str
    template_id: int
    organization_id: int
    deleted_by_id: int
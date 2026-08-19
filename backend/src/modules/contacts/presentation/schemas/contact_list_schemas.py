from datetime import datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field

from src.shared.schemas.base_schema import (
    BaseSchema,
    DomainEmail,
    DomainString,
    NameString,
    field_validator,
)


class CreateContactListRequestSchema(BaseSchema):
    name: NameString = Field(min_length=1)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("name", mode="after")
    @classmethod
    def reject_empty_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Name must not be empty")
        return value


class UpdateContactListRequestSchema(BaseSchema):
    name: NameString | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("name", mode="after")
    @classmethod
    def reject_empty_name(cls, value: str | None) -> str | None:
        if value is not None and not value:
            raise ValueError("Name must not be empty")
        return value


class ContactListResponseSchema(BaseSchema):
    uuid: str
    name: str
    description: str | None = None
    field_definitions: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    contact_count: int = 0
    verified_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ContactListListResponseSchema(BaseSchema):
    items: list[ContactListResponseSchema]
    total: int
    limit: int
    offset: int


class ContactResponseSchema(BaseSchema):
    uuid: str
    email: str
    metadata: dict | None = None
    subscribed: bool = True
    unsubscribed_at: datetime | None = None
    last_contacted_at: datetime | None = None
    status: str = "active"
    verification_status: str = "unverified"
    verification_sub_status: str | None = None
    verification_score: int | None = None
    verification_details: dict | None = None
    verified_at: datetime | None = None
    bounce_risk: str | None = None
    last_bounced_at: datetime | None = None
    archived_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreateContactRequestSchema(BaseSchema):
    email: DomainEmail
    metadata: dict[str, str] | None = None
    subscribed: bool = True


class UpdateContactRequestSchema(BaseSchema):
    email: DomainEmail | None = None
    metadata: dict[str, str | None] | None = None
    subscribed: bool | None = None
    status: (
        Literal["active", "bounced", "unsubscribed", "suppressed", "archived"] | None
    ) = None


class BulkVerifyContactsRequestSchema(BaseSchema):
    contact_uuids: list[str] = Field(min_length=1, max_length=200)


class ContactListItemsResponseSchema(BaseSchema):
    items: list[ContactResponseSchema]
    total: int
    limit: int
    offset: int


class ImportResponseSchema(BaseSchema):
    total: int
    imported: int
    updated: int
    errors: list[dict] = Field(default_factory=list)
    duplicates: int = 0
    skipped: int = 0
    reasons: dict[str, int] = Field(default_factory=dict)


class SheetTabSchema(BaseSchema):
    title: str
    sheet_id: int
    row_count: int


class SheetTabsResponseSchema(BaseSchema):
    tabs: list[SheetTabSchema]


class SheetTabsRequestSchema(BaseSchema):
    sheet_url: str = Field(min_length=20, max_length=2048)


class SheetImportRequestSchema(BaseSchema):
    sheet_url: str = Field(min_length=20, max_length=2048)
    tab: str = Field(min_length=1, max_length=200)

    @field_validator("sheet_url", "tab", mode="before")
    @classmethod
    def strip_sheet_fields(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value


class ContactActivityResponseSchema(BaseSchema):
    uuid: str
    activity_type: str
    description: str | None = None
    metadata: dict | None = None
    created_at: datetime | None = None


class ContactTimelineResponseSchema(BaseSchema):
    items: list[ContactActivityResponseSchema]
    total: int
    limit: int
    offset: int

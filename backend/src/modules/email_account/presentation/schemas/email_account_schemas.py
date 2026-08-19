from datetime import date, datetime

from typing import Any

from src.shared.schemas import BaseSchema, DomainEmail, DomainString, NameString, Field, field_validator, model_validator


class ConnectSmtpRequestSchema(BaseSchema):
    email: DomainEmail
    sender_name: NameString | None = None
    smtp_host: str = Field(min_length=1, max_length=253)
    smtp_port: int = Field(ge=1, le=65535)
    smtp_username: str = Field(min_length=1, max_length=255)
    smtp_password: str = Field(min_length=1, max_length=255)
    imap_host: str | None = Field(default=None, max_length=253)
    imap_port: int | None = Field(default=None, ge=1, le=65535)
    reply_to: DomainString | None = None
    signature: DomainString | None = None

    @field_validator("smtp_host", mode="before")
    @classmethod
    def validate_smtp_host(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("SMTP host is required")
        value = value.strip()
        if any(char.isspace() for char in value) or "://" in value:
            raise ValueError("Enter an SMTP hostname such as smtp.example.com")
        return value

    @field_validator("imap_host", mode="before")
    @classmethod
    def validate_imap_host(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return None
        if any(char.isspace() for char in value) or "://" in value:
            raise ValueError("Enter an IMAP hostname such as imap.example.com")
        return value

    @field_validator("smtp_username", mode="before")
    @classmethod
    def clean_smtp_username(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("SMTP username is required")
        return value.strip()

    @field_validator("smtp_password", mode="before")
    @classmethod
    def validate_smtp_password(cls, value: Any) -> Any:
        if not isinstance(value, str) or not value:
            raise ValueError("SMTP password is required")
        return value

    @field_validator("sender_name", mode="before")
    @classmethod
    def clean_sender_name(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            if not any(char.isalpha() for char in value):
                raise ValueError("Sender name must contain at least one letter")
        return value

    @model_validator(mode="after")
    def validate_imap_pair(self):
        if self.imap_port is not None and not self.imap_host:
            raise ValueError("IMAP host is required when an IMAP port is provided")
        return self


class VerifySmtpRequestSchema(BaseSchema):
    code: str


class ConnectOAuthRequestSchema(BaseSchema):
    provider: DomainString
    account_uuid: str | None = None


class UpdateEmailAccountRequestSchema(BaseSchema):
    sender_name: NameString | None = None
    sending_limit: int | None = None
    reply_to: DomainString | None = None
    signature: DomainString | None = None


class EmailAccountResponseSchema(BaseSchema):
    uuid: str
    organization_id: int
    provider: str
    email: str
    sender_name: str | None = None
    status: str
    health_status: str
    health_score: int | None = None
    health_details: dict | None = None
    daily_sent_count: int = 0
    last_sent_date: date | None = None
    sending_limit: int = 100
    reply_to: str | None = None
    signature: str | None = None
    last_used_at: datetime | None = None
    created_at: datetime | None = None


class EmailAccountConnectResponseSchema(BaseSchema):
    uuid: str
    email: str
    provider: str
    status: str
    message: str | None = None


class EmailAccountListResponseSchema(BaseSchema):
    items: list[EmailAccountResponseSchema]
    total: int
    limit: int
    offset: int

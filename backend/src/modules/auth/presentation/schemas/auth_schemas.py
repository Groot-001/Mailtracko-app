from datetime import datetime
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from src.shared.schemas.base_schema import BaseSchema, DomainEmail, DomainString, NameString


class RegisterRequest(BaseSchema):
    full_name: NameString = Field(min_length=1)
    email: DomainEmail
    password: str = Field(min_length=1, max_length=128)
    invite_token: DomainString | None = None


class LoginRequest(BaseSchema):
    email: DomainEmail
    password: str = Field(min_length=1, max_length=128)


class UpdateProfileRequest(BaseSchema):
    full_name: NameString | None = None
    theme: Literal["light", "dark"] | None = None
    profile_image: str | None = None
    timezone: str | None = None
    phone: str | None = None
    country_code: str | None = None
    location: str | None = None

    @field_validator("profile_image")
    @classmethod
    def validate_profile_image(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 500:
            raise ValueError("Profile image URL cannot exceed 500 characters")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 100:
            raise ValueError("Timezone cannot exceed 100 characters")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 50:
            raise ValueError("Phone cannot exceed 50 characters")
        return value

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 10:
            raise ValueError("Country code cannot exceed 10 characters")
        return value

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) > 255:
            raise ValueError("Location cannot exceed 255 characters")
        return value


class VerifyEmailRequest(BaseSchema):
    token: DomainString


class ForgotPasswordRequest(BaseSchema):
    email: DomainEmail


class ForgotPasswordVerifyRequest(BaseSchema):
    token: DomainString
    new_password: DomainString


class ForgotPasswordCodeVerifyRequest(BaseSchema):
    token: DomainString


class ForgotPasswordResetRequest(BaseSchema):
    reset_challenge: DomainString
    new_password: DomainString


class UserResponse(BaseSchema):
    uuid: DomainString
    full_name: DomainString | None = None
    email: DomainEmail
    profile_image: str | None = None
    timezone: str | None = None
    phone: str | None = None
    country_code: str | None = None
    location: str | None = None
    theme: DomainString
    is_2fa_enabled: bool = False
    has_password: bool = True
    created_at: DomainString | None = None

    model_config = ConfigDict(from_attributes=True)


class UserAccountSummarySchema(BaseSchema):
    role: str | None = None
    organization_name: str | None = None
    organization_uuid: str | None = None
    member_status: str | None = None
    account_status: str | None = None
    plan: str | None = None


class UserActivityResponseSchema(BaseSchema):
    uuid: str
    activity_type: str
    description: str | None = None
    metadata: dict | None = None
    created_at: datetime | None = None


class UserActivityListResponseSchema(BaseSchema):
    items: list[UserActivityResponseSchema]
    total: int
    limit: int
    offset: int


class ChangePasswordRequest(BaseSchema):
    current_password: str
    new_password: str
    confirm_password: str


class SetupTotpResponseSchema(BaseSchema):
    secret: str
    provisioning_uri: str
    qr_code: str
    recovery_codes: list[str]


class VerifyTotpRequest(BaseSchema):
    code: str


class Verify2FALoginRequest(BaseSchema):
    temp_token: str | None = None
    code: str




from datetime import datetime
from typing import Any, Literal
import re
from urllib.parse import urlparse

from pydantic import Field

from src.modules.organization.domain.enums.organization_enums import (
    OrganizationIndustrySectorEnum,
    OrganizationRoleCodeEnum,
    OrganizationSourceEnum,
    OrganizationThemeEnum,
)
from src.shared.schemas import BaseSchema, DomainEmail, DomainString, NameString, field_validator, model_validator


OrganizationSize = Literal[
    "1-10 employees",
    "11-50 employees",
    "51-200 employees",
    "201-500 employees",
    "500-1000 employees",
    "1000+ employees",
]
MonthlyEmailVolume = Literal[
    "< 5,000",
    "5,000 - 25,000",
    "25,000 - 100,000",
    "100,000 - 500,000",
    "500,000+",
]
_DOMAIN_RE = re.compile(r"^(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.I)


class CreateOrganizationRequestSchema(BaseSchema):
    """
    Request schema for creating organization during onboarding.
    """

    name: NameString = Field(min_length=2)
    website_url: str | None = Field(default=None, max_length=200)
    org_size: OrganizationSize | None = None
    monthly_email_volume: MonthlyEmailVolume | None = None
    domain_email: str | None = Field(default=None, max_length=253)
    org_logo: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=250)
    industry_sector: OrganizationIndustrySectorEnum | None = None
    source: OrganizationSourceEnum | None = None
    theme: OrganizationThemeEnum
    timezone: DomainString | None = None
    onboarding_skipped: bool = False

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: Any) -> Any:
        """
        Trims organization name and prevents empty organization name.
        """
        if isinstance(value, str):
            value = value.strip()

        return value

    @field_validator("website_url", mode="before")
    @classmethod
    def validate_website_url(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a valid website URL starting with http:// or https://")
        return value

    @field_validator("domain_email", mode="before")
    @classmethod
    def validate_company_domain(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        value = value.strip().lower()
        if not value:
            return None
        if not _DOMAIN_RE.fullmatch(value):
            raise ValueError("Enter a valid company domain, for example yourcompany.com")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("theme", mode="before")
    @classmethod
    def empty_theme_to_light(cls, value: Any) -> Any:
        """
        Uses light theme when frontend sends empty theme.
        """
        if isinstance(value, str):
            value = value.strip()
            return value or OrganizationThemeEnum.LIGHT.value

        return value

    @field_validator("timezone", mode="before")
    @classmethod
    def empty_timezone_to_utc(cls, value: Any) -> Any:
        """
        Uses UTC timezone when frontend sends empty timezone.
        """
        if isinstance(value, str):
            value = value.strip()
            return value or "UTC"

        return value

    @model_validator(mode="after")
    def validate_required_onboarding_steps(self):
        """Require every completed wizard step unless the user explicitly skipped onboarding."""
        if self.onboarding_skipped:
            return self

        required = {
            "website_url": (self.website_url, "Website URL is required"),
            "org_size": (self.org_size, "Organization size is required"),
            "monthly_email_volume": (self.monthly_email_volume, "Monthly email volume is required"),
            "domain_email": (self.domain_email, "Company email domain is required"),
            "industry_sector": (self.industry_sector, "Industry sector is required"),
            "source": (self.source, "Discovery source is required"),
        }
        missing = {field: message for field, (value, message) in required.items() if value is None}
        if missing:
            raise ValueError(next(iter(missing.values())))
        return self


class CreateOrganizationResponseSchema(BaseSchema):
    """
    Response schema after creating organization.
    """

    uuid: str
    name: str
    website_url: str | None = None
    org_size: str | None = None
    monthly_email_volume: str | None = None
    domain_email: str | None = None
    org_logo: str | None = None
    description: str | None = None
    industry_sector: str | None = None
    source: str | None = None
    theme: str
    timezone: DomainString | None = None
    status: str
    owner_id: int
    member_uuid: str | None = None
    role_code: str | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class CurrentOrganizationDetailsResponseSchema(BaseSchema):
    """
    Response schema for organization details.
    """

    uuid: str
    name: str
    website_url: str | None = None
    org_size: str | None = None
    monthly_email_volume: str | None = None
    domain_email: str | None = None
    org_logo: str | None = None
    description: str | None = None
    industry_sector: str | None = None
    source: str | None = None
    theme: str
    timezone: DomainString | None = None
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    deletion_requested_at: datetime | None = None
    deletion_requested_by_id: int | None = None
    scheduled_deletion_at: datetime | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class EditOrganizationRequestSchema(BaseSchema):
    """
    Request schema for editing organization details.
    """

    name: NameString | None = Field(default=None, min_length=2)
    website_url: str | None = Field(default=None, max_length=200)
    org_size: OrganizationSize | None = None
    monthly_email_volume: MonthlyEmailVolume | None = None
    domain_email: str | None = Field(default=None, max_length=253)
    org_logo: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=250)
    industry_sector: OrganizationIndustrySectorEnum | None = None
    source: OrganizationSourceEnum | None = None
    theme: OrganizationThemeEnum | None = None
    timezone: DomainString | None = None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value: Any) -> Any:
        """
        Trims organization name when editing.
        """
        if isinstance(value, str):
            value = value.strip()
            return value or None

        return value

    @field_validator("website_url", mode="before")
    @classmethod
    def validate_website_url(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a valid website URL starting with http:// or https://")
        return value

    @field_validator("domain_email", mode="before")
    @classmethod
    def validate_company_domain(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        value = value.strip().lower()
        if not value:
            return None
        if not _DOMAIN_RE.fullmatch(value):
            raise ValueError("Enter a valid company domain, for example yourcompany.com")
        return value

    @field_validator("org_logo", mode="before")
    @classmethod
    def validate_org_logo(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter a valid logo URL starting with http:// or https://")
        return value

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("timezone", mode="before")
    @classmethod
    def clean_timezone(cls, value: Any) -> Any:
        """
        Trims timezone when editing.
        """
        if isinstance(value, str):
            value = value.strip()
            return value or None

        return value

class OrganizationDeletionDataSummarySchema(BaseSchema):
    """
    Data summary shown before requesting organization deletion.
    """

    team_members: int
    active_members: int
    pending_invitations: int
    campaigns: int = 0
    stored_contacts: int = 0
    files_and_attachments: int = 0


class OrganizationDeletionSummaryResponseSchema(BaseSchema):
    """
    Response schema for organization deletion summary.
    """

    organization_uuid: str
    organization_name: str
    grace_period_days: int
    data_summary: OrganizationDeletionDataSummarySchema

class RequestOrganizationDeletionResponseSchema(BaseSchema):
    """
    Response schema after requesting organization deletion.
    """

    uuid: str
    name: str
    deletion_requested_at: datetime | None = None
    deletion_requested_by_id: int | None = None
    scheduled_deletion_at: datetime | None = None
    message: str

    model_config = {"from_attributes": True, "extra": "ignore"}

class OrganizationActivityResponseSchema(BaseSchema):
    """
    Response schema for a single recent organization activity.
    """

    uuid: str
    activity_type: str
    title: str
    actor_user_id: int | None = None
    target_user_id: int | None = None
    target_email: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True, "extra": "ignore"}


class OrganizationActivityListResponseSchema(BaseSchema):
    """
    Paginated response schema for recent organization activities.
    """

    items: list[OrganizationActivityResponseSchema]
    total: int
    limit: int
    offset: int

class OrganizationMemberUserSchema(BaseSchema):
    """
    User details embedded in an organization-member listing response.
    """

    uuid: str
    email: str
    avatar_bg: str | None = None
    full_name: str | None = None
    avatar: str | None = None

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }


class OrganizationMemberResponseSchema(BaseSchema):
    """
    Schema for a single organization member row.
    """

    id: int
    uuid: str
    organization_id: int
    user_id: int
    role_code: str
    status: str
    invited_by_id: int | None = None
    joined_at: datetime | None = None
    permissions: dict[str, bool] = Field(default_factory=dict)
    user: OrganizationMemberUserSchema | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class OrganizationMemberListResponseSchema(BaseSchema):
    """
    Paginated container for organization-member listings.
    """

    items: list[OrganizationMemberResponseSchema]
    total: int
    limit: int
    offset: int


class InviteOrganizationMemberRequestSchema(BaseSchema):
    """
    Request schema for inviting an organization member.
    """

    email: DomainEmail
    role_code: OrganizationRoleCodeEnum = OrganizationRoleCodeEnum.MEMBER

    @field_validator("role_code", mode="before")
    @classmethod
    def empty_role_to_member(cls, value: Any) -> Any:
        """
        Uses member role when frontend sends empty role.
        """
        if isinstance(value, str):
            value = value.strip()
            return value or OrganizationRoleCodeEnum.MEMBER.value

        return value

    @field_validator("role_code")
    @classmethod
    def validate_invitable_role(
        cls,
        value: OrganizationRoleCodeEnum,
    ) -> OrganizationRoleCodeEnum:
        """
        Owner cannot be invited.
        Owner is created only during organization creation.
        """
        if value == OrganizationRoleCodeEnum.OWNER:
            raise ValueError("Owner role cannot be invited")

        return value


class InviteOrganizationMemberResponseSchema(BaseSchema):
    """
    Response schema after creating organization invitation.
    """

    uuid: str
    email: str
    role_code: str
    status: str
    expires_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class OrganizationInvitationResponseSchema(BaseSchema):
    """
    Response schema for organization invitation.
    """

    uuid: str
    email: str
    role_code: str
    status: str
    invited_by_id: int
    expires_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
    accepted_at: datetime | None = None
    declined_at: datetime | None = None
    revoked_at: datetime | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class OrganizationInvitationListResponseSchema(BaseSchema):
    """
    Paginated container for organization invitation listings.
    """

    items: list[OrganizationInvitationResponseSchema]
    total: int
    limit: int
    offset: int




class ValidateOrganizationInvitationResponseSchema(BaseSchema):
    """Public invitation details needed before account creation."""

    email: str
    organization_name: str
    role_code: str
    expires_at: datetime

class AcceptOrganizationInvitationRequestSchema(BaseSchema):
    """
    Request schema for accepting organization invitation.
    """

    token: DomainString

    @field_validator("token", mode="before")
    @classmethod
    def clean_token(cls, value: Any) -> Any:
        """
        Trims invitation token.
        """
        if isinstance(value, str):
            value = value.strip()

        return value


class AcceptOrganizationInvitationResponseSchema(BaseSchema):
    """
    Response schema after accepting organization invitation.
    """

    uuid: str
    email: str
    status: str
    organization_id: int
    role_code: str
    member_uuid: str | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class DeclineOrganizationInvitationRequestSchema(BaseSchema):
    """
    Request schema for declining organization invitation.
    """

    token: DomainString

    @field_validator("token", mode="before")
    @classmethod
    def clean_token(cls, value: Any) -> Any:
        """
        Trims invitation token.
        """
        if isinstance(value, str):
            value = value.strip()

        return value


class DeclineOrganizationInvitationResponseSchema(BaseSchema):
    """
    Response schema after declining organization invitation.
    """

    uuid: str
    email: str
    status: str

    model_config = {"from_attributes": True, "extra": "ignore"}


class ResendOrganizationInvitationResponseSchema(BaseSchema):
    """Response schema after resending an organization invitation."""

    uuid: str
    email: str
    role_code: str
    status: str
    expires_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True, "extra": "ignore"}


class RevokeOrganizationInvitationResponseSchema(BaseSchema):
    """
    Response schema after revoking organization invitation.
    """

    uuid: str
    email: str
    role_code: str
    status: str

    model_config = {"from_attributes": True, "extra": "ignore"}


class RemoveOrganizationMemberResponseSchema(BaseSchema):
    """
    Response schema after removing organization member.
    """

    uuid: str
    user_id: int
    role_code: str

    model_config = {"from_attributes": True, "extra": "ignore"}


class AccountDeletionImpactResponseSchema(BaseSchema):
    """
    Response schema for account deletion impact.
    """

    is_organization_member: bool
    is_owner: bool
    will_delete_organization: bool
    message: str


class OrganizationOnboardingStatusResponseSchema(BaseSchema):
    """
    Response schema for organization onboarding status.
    """

    has_completed_onboarding: bool
    needs_onboarding: bool
    has_pending_invitation: bool = False
    invitation_uuid: str | None = None
    organization_uuid: str | None = None
    role_code: str | None = None
    message: str

    model_config = {"from_attributes": True, "extra": "ignore"}

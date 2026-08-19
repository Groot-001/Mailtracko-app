from enum import StrEnum


class OrganizationStatusEnum(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class OrganizationMemberStatusEnum(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REMOVED = "removed"


class OrganizationRoleCodeEnum(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class OrganizationInvitationStatusEnum(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVOKED = "revoked"
    EXPIRED = "expired"


class OrganizationIndustrySectorEnum(StrEnum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    ECOMMERCE = "ecommerce"
    REAL_ESTATE = "real_estate"
    CONSULTING = "consulting"
    MANUFACTURING = "manufacturing"
    OTHERS = "others"


class OrganizationSourceEnum(StrEnum):
    REFERRAL = "referral"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    MARKETPLACE = "marketplace"
    NEWSLETTER = "newsletter"
    EVENTS_WEBINAR = "events_webinar"
    SOCIAL_MEDIA = "social_media"
    OTHERS = "others"


class OrganizationThemeEnum(StrEnum):
    DARK = "dark"
    LIGHT = "light"
    
class OrganizationActivityTypeEnum(StrEnum):
    ORGANIZATION_CREATED = "organization_created"
    ORGANIZATION_UPDATED = "organization_updated"
    ORGANIZATION_DELETION_REQUESTED = "organization_deletion_requested"

    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"

    INVITATION_SENT = "invitation_sent"
    INVITATION_ACCEPTED = "invitation_accepted"
    INVITATION_DECLINED = "invitation_declined"
    INVITATION_REVOKED = "invitation_revoked"
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from src.modules.organization.domain.enums.organization_enums import (
    OrganizationStatusEnum,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class OrganizationEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """
    Entity representing a MailTracko organization/workspace.
    """

    name: str = field(
        metadata={
            "description": "Organization/workspace name",
        }
    )

    website_url: str | None = field(
        default=None,
        metadata={
            "description": "Organization website URL",
        },
    )

    org_size: str | None = field(
        default=None,
        metadata={
            "description": "Organization size selected during onboarding",
        },
    )
    
    monthly_email_volume: str | None = field(
        default=None,
        metadata={
            "description": "Approximate number of outbound emails the organization expects to send per month",
            "index": True,
        },
    )

    domain_email: str | None = field(
        default=None,
        metadata={
            "description": "Organization company email domain",
        },
    )

    org_logo: str | None = field(
        default=None,
        metadata={
            "description": "Organization logo file URL or storage path",
        },
    )

    description: str | None = field(
        default=None,
        metadata={
            "description": "Short description/about the organization",
        },
    )

    industry_sector: str | None = field(
        default=None,
        metadata={
            "description": "Industry sector selected during onboarding",
            "index": True,
        },
    )

    source: str | None = field(
        default=None,
        metadata={
            "description": "How the organization/user heard about MailTracko",
            "index": True,
        },
    )

    theme: str = field(
        default="light",
        metadata={
            "description": "Workspace theme preference such as light or dark",
        },
    )

    timezone: str | None = field(
        default="UTC",
        metadata={
            "description": "Organization timezone",
            "index": True,
        },
    )

    owner_id: int = field(
        metadata={
            "description": "Owner user id from sys_auth_users",
            "index": True,
            "on_delete": "restrict",
        }
    )

    status: str = field(
        default="active",
        metadata={
            "description": "Organization status such as active or suspended",
            "index": True,
        },
    )

    deletion_requested_at: datetime | None = field(
        default=None,
        metadata={
            "description": "Date and time when organization deletion was requested",
        },
    )

    deletion_requested_by_id: int | None = field(
        default=None,
        metadata={
            "description": "User id who requested organization deletion",
            "index": True,
            "on_delete": "set_null",
        },
    )

    scheduled_deletion_at: datetime | None = field(
        default=None,
        metadata={
            "description": "Date and time when organization should be deleted after grace period",
            "index": True,
        },
    )

    def is_active(self) -> bool:
        """
        Returns True if organization status is active.
        """
        return self.status == OrganizationStatusEnum.ACTIVE.value

    def is_suspended(self) -> bool:
        """
        Returns True if organization status is suspended.
        """
        return self.status == OrganizationStatusEnum.SUSPENDED.value

    def request_deletion(
        self,
        requested_by_id: int,
        grace_period_days: int,
    ) -> None:
        """
        Schedules organization deletion after grace period.

        If deletion is already scheduled, do not reset the timer.
        """
        if self.scheduled_deletion_at is not None:
            return

        now = datetime.now(UTC)

        self.deletion_requested_at = now
        self.deletion_requested_by_id = requested_by_id
        self.scheduled_deletion_at = now + timedelta(days=grace_period_days)
        self.mark_updated()
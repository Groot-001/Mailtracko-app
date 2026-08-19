from dataclasses import dataclass, field
from datetime import datetime

from src.modules.organization.domain.enums.organization_enums import (
    OrganizationMemberStatusEnum,
    OrganizationRoleCodeEnum,
)
from src.shared.domain.entity.base_entity import BaseEntity
from src.shared.domain.mixin.audit_mixin import AuditMixin
from src.shared.domain.mixin.soft_delete_mixin import SoftDeleteMixin


@dataclass(kw_only=True)
class OrganizationMemberEntity(BaseEntity, AuditMixin, SoftDeleteMixin):
    """
    Entity representing a user membership inside an organization.
    """

    organization_id: int = field(
        metadata={
            "description": "Organization id",
            "index": True,
            "on_delete": "cascade",
        }
    )

    user_id: int = field(
        metadata={
            "description": "User id from sys_auth_users",
            "unique": True,
            "index": True,
            "on_delete": "cascade",
        }
    )

    role_code: str = field(
        metadata={
            "description": "Member role code such as owner, admin, or member",
            "index": True,
        }
    )

    status: str = field(
        default="active",
        metadata={
            "description": "Member status such as active, inactive, or removed",
            "index": True,
        },
    )

    invited_by_id: int | None = field(
        default=None,
        metadata={
            "description": "User id who invited this member",
            "index": True,
            "on_delete": "set_null",
        },
    )

    joined_at: datetime | None = field(
        default=None,
        metadata={
            "description": "Date and time when the user joined the organization",
        },
    )

    permissions: dict[str, bool] = field(
        default_factory=dict,
        metadata={
            "description": "Explicit workspace permission overrides for this member",
        },
    )

    def is_active(self) -> bool:
        """
        Returns True if member status is active.
        """
        return self.status == OrganizationMemberStatusEnum.ACTIVE.value

    def is_owner(self) -> bool:
        """
        Returns True if member has owner role.
        """
        return self.role_code == OrganizationRoleCodeEnum.OWNER.value

    def is_admin(self) -> bool:
        """
        Returns True if member has admin role.
        """
        return self.role_code == OrganizationRoleCodeEnum.ADMIN.value

    def is_member(self) -> bool:
        """
        Returns True if member has member role.
        """
        return self.role_code == OrganizationRoleCodeEnum.MEMBER.value

    def can_manage_members(self) -> bool:
        """
        Returns True if member can manage other members (owner or admin).
        """
        return self.is_owner() or self.is_admin()

    def can_edit_organization(self) -> bool:
        """
        Returns True if member can edit organization settings (owner only).
        """
        return self.is_owner()
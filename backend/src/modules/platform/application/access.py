from dataclasses import dataclass

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.settings import config
from src.modules.organization.infrastructure.models.organization_member_model import (
    OrganizationMemberModel,
)
from src.modules.organization.infrastructure.models.organization_model import (
    OrganizationModel,
)
from src.modules.platform.infrastructure.models.platform_models import AuditLogModel
from src.modules.platform.application.workspace_permissions import effective_workspace_permissions
from src.shared.exceptions.base_exceptions import ForbiddenError


@dataclass(frozen=True)
class WorkspaceContext:
    organization: OrganizationModel
    member: OrganizationMemberModel


def is_platform_admin_email(email: str | None) -> bool:
    if not email:
        return False
    allowed = {
        item.strip().lower() for item in config.SUPERADMIN_EMAILS if item.strip()
    }
    return email.strip().lower() in allowed


def require_platform_admin(request: Request) -> None:
    user = getattr(request.state, "user", None)
    if not user or not is_platform_admin_email(user.email):
        raise ForbiddenError(error="Platform administrator access is required")


async def load_workspace_context(
    request: Request,
    session: AsyncSession,
    allowed_roles: set[str] | None = None,
    required_permissions: set[str] | None = None,
) -> WorkspaceContext:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise ForbiddenError(error="A valid workspace membership is required")

    requested_org_uuid = request.headers.get("X-Organization-UUID")
    # Resolve only memberships whose workspace is currently usable. Without this
    # join, a user belonging to multiple organizations could be blocked simply
    # because their oldest membership points to a suspended workspace.
    stmt = (
        select(OrganizationMemberModel)
        .join(
            OrganizationModel,
            OrganizationModel.id == OrganizationMemberModel.organization_id,
        )
        .where(
            OrganizationMemberModel.user_id == user_id,
            OrganizationMemberModel.status == "active",
            OrganizationMemberModel.deleted_at.is_(None),
            OrganizationModel.deleted_at.is_(None),
            OrganizationModel.status == "active",
        )
    )
    if requested_org_uuid:
        stmt = stmt.where(OrganizationModel.uuid == requested_org_uuid)

    member = (
        (await session.execute(stmt.order_by(OrganizationMemberModel.id.asc())))
        .scalars()
        .first()
    )
    if not member:
        raise ForbiddenError(error="User does not belong to an active organization")

    organization = await session.get(OrganizationModel, member.organization_id)
    if not organization or organization.deleted_at is not None:
        raise ForbiddenError(error="Organization is unavailable")
    if organization.status != "active":
        raise ForbiddenError(error="Organization is suspended")

    if allowed_roles and member.role_code not in allowed_roles:
        raise ForbiddenError(error="Your workspace role does not allow this action")

    permissions = effective_workspace_permissions(member)
    if required_permissions and not all(permissions.get(key, False) for key in required_permissions):
        raise ForbiddenError(error="Your workspace permissions do not allow this action")

    request.state.organization_permissions = permissions
    request.state.organization_id = organization.id
    request.state.organization_uuid = organization.uuid
    request.state.organization_role_code = member.role_code
    request.state.organization_member_id = member.id
    return WorkspaceContext(organization=organization, member=member)


async def write_audit_log(
    session: AsyncSession,
    request: Request,
    *,
    action: str,
    resource_type: str,
    resource_uuid: str | None = None,
    metadata: dict | None = None,
    organization_id: int | None = None,
) -> AuditLogModel:
    entry = AuditLogModel(
        organization_id=organization_id,
        actor_user_id=getattr(request.state, "user_id", None),
        action=action,
        resource_type=resource_type,
        resource_uuid=resource_uuid,
        metadata_=metadata,
        ip_address=getattr(request.state, "ip_address", None),
        user_agent=getattr(request.state, "user_agent", None),
    )
    session.add(entry)
    await session.flush()
    return entry

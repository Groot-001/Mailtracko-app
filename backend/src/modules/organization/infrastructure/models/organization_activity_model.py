from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import SoftDeleteMixinModel


class OrganizationActivityModel(BaseModel, AuditMixinModel, SoftDeleteMixinModel):
    """
    SQLAlchemy model representing recent organization activity.
    """

    __tablename__ = "org_organization_activities"

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    activity_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    target_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
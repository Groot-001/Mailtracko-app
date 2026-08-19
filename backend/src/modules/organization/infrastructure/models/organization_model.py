from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import SoftDeleteMixinModel


class OrganizationModel(BaseModel, AuditMixinModel, SoftDeleteMixinModel):
    """
    SQLAlchemy model representing a MailTracko organization/workspace.
    """

    __tablename__ = "org_organizations"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    org_size: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    monthly_email_volume: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    domain_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    org_logo: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    industry_sector: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="light",
    )

    timezone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default="UTC",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deletion_requested_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    scheduled_deletion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import (
    AuditMixinModel,
)
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import (
    SoftDeleteMixinModel,
)


class TemplateModel(
    BaseModel,
    AuditMixinModel,
    SoftDeleteMixinModel,
):
    """
    SQLAlchemy model representing a system or custom email template.
    """

    __tablename__ = "templates"

    __table_args__ = (
        Index(
            "ix_templates_organization_status",
            "organization_id",
            "status",
        ),
        Index(
            "ix_templates_organization_deleted_at",
            "organization_id",
            "deleted_at",
        ),
        Index(
            "ix_templates_organization_default",
            "organization_id",
            "is_default",
        ),
        Index(
            "ix_templates_type_category",
            "template_type",
            "category_id",
        ),
        Index(
            "ix_templates_updated_at",
            "updated_at",
        ),
        Index(
            "ix_templates_created_at",
            "created_at",
        ),
        Index(
            "uq_templates_one_default_per_organization",
            "organization_id",
            unique=True,
            postgresql_where=text(
                "is_default = true "
                "AND template_type = 'custom' "
                "AND deleted_at IS NULL"
            ),
        ),
    )

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "org_organizations.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "template_categories.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    source_template_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "templates.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    preheader: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    body_html: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    from_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    from_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    template_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="custom",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    smart_personalization_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
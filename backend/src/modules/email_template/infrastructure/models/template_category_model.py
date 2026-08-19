from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import (
    SoftDeleteMixinModel,
)


class TemplateCategoryModel(
    BaseModel,
    AuditMixinModel,
    SoftDeleteMixinModel,
):
    """
    SQLAlchemy model representing a system template category.
    """

    __tablename__ = "template_categories"

    __table_args__ = (
        Index(
            "ix_template_categories_created_at",
            "created_at",
        ),
        Index(
            "uq_template_categories_org_name",
            "organization_id",
            "name",
            unique=True,
        ),
    )

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("org_organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
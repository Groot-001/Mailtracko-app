from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import (
    SoftDeleteMixinModel,
)


class TemplateAssetModel(
    BaseModel,
    AuditMixinModel,
    SoftDeleteMixinModel,
):
    """
    SQLAlchemy model representing an inline image or template attachment.
    """

    __tablename__ = "template_assets"

    __table_args__ = (
        Index(
            "ix_template_assets_template_usage",
            "template_id",
            "usage",
        ),
        Index(
            "ix_template_assets_organization_deleted_at",
            "organization_id",
            "deleted_at",
        ),
        Index(
            "ix_template_assets_created_at",
            "created_at",
        ),
    )

    template_id: Mapped[int] = mapped_column(
        ForeignKey(
            "templates.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "org_organizations.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )

    file_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    asset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    usage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "sys_auth_users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import SoftDeleteMixinModel


class ContactListModel(BaseModel, AuditMixinModel, SoftDeleteMixinModel):
    """SQLAlchemy model for the contact_lists table."""

    __tablename__ = "contact_lists"

    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_definitions: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ContactModel(BaseModel):
    """SQLAlchemy model for the contact_contacts table."""

    __tablename__ = "contact_contacts"

    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    contact_list_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contact_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    subscribed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    unsubscribed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="unverified", index=True
    )
    verification_sub_status: Mapped[str | None] = mapped_column(
        String(80), nullable=True
    )
    verification_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bounce_risk: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )
    last_bounced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint("contact_list_id", "email", name="uq_contact_list_email"),
    )


class ContactActivityModel(BaseModel):
    """SQLAlchemy model for the contact_activities table."""

    __tablename__ = "contact_activities"

    contact_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contact_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)


class ContactImportLogModel(BaseModel, AuditMixinModel):
    """SQLAlchemy model for the contact_import_logs table."""

    __tablename__ = "contact_import_logs"

    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    contact_list_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("contact_lists.id", ondelete="CASCADE"),
        nullable=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    column_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )

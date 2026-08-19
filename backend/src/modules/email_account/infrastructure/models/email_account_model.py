
from datetime import datetime, date

import sqlalchemy as sa
from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.audit_mixin_model import AuditMixinModel
from src.shared.infrastructure.model.base_model import BaseModel
from src.shared.infrastructure.model.soft_delete_mixin_model import SoftDeleteMixinModel

class EmailAccountModel(BaseModel, AuditMixinModel, SoftDeleteMixinModel):
    __tablename__ = "email_accounts"

    organization_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    __table_args__ = (sa.UniqueConstraint("organization_id", "email", name="uq_email_org_email"),)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending_verification", index=True)
    smtp_config_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("email_smtp_configs.id", ondelete="SET NULL"), nullable=True)
    oauth_config_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("email_oauth_configs.id", ondelete="SET NULL"), nullable=True)
    health_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    daily_sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_sent_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sending_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    reply_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    health_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class SmtpConfigModel(BaseModel):
    __tablename__ = "email_smtp_configs"

    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False)
    smtp_username: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    imap_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_code_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OauthConfigModel(BaseModel):
    __tablename__ = "email_oauth_configs"

    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    organization_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("org_organizations.id", ondelete="CASCADE"), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(50), nullable=True)

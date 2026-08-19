from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.base_model import BaseModel


class UserSessionModel(BaseModel):
    """SQLAlchemy model for the sys_auth_user_sessions table.

    Tracks active user sessions with device metadata and revocation support.
    """

    __tablename__ = "sys_auth_user_sessions"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"), nullable=True
    )

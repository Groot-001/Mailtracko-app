from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.base_model import BaseModel


class UserAccountModel(BaseModel):
    __tablename__ = "sys_auth_user_accounts"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_password_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

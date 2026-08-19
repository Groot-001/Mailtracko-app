from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.base_model import BaseModel


class UserTotpSecretModel(BaseModel):
    __tablename__ = "auth_user_totp_secrets"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_auth_users.id", ondelete="CASCADE"), nullable=False, unique=True,
    )
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

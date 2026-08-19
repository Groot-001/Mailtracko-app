import sqlalchemy as sa
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.model.base_model import BaseModel


class UserActivityModel(BaseModel):
    __tablename__ = "auth_user_activities"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_auth_users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

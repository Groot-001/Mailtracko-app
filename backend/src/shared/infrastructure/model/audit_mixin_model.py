from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixinModel:
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_auth_users.id", ondelete="SET NULL"),
        nullable=True,
    )

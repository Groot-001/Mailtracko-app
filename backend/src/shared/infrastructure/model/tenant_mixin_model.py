from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class TenantMixinModel:
    organization_id: Mapped[int | None] = mapped_column(
        ForeignKey("organization_organizations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

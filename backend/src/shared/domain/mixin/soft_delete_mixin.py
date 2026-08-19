from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class SoftDeleteMixin:
    deleted_at: datetime | None = None

    def soft_delete(self):
        self.deleted_at = datetime.now(UTC)

    def restore(self):
        self.deleted_at = None

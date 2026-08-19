from dataclasses import dataclass


@dataclass
class AuditMixin:
    created_by_id: int | None = None
    updated_by_id: int | None = None

    def set_created_by(self, user_id: int):
        self.created_by_id = user_id

    def set_updated_by(self, user_id: int):
        self.updated_by_id = user_id

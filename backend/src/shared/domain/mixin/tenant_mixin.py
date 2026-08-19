from dataclasses import dataclass


@dataclass
class TenantMixin:
    organization_id: int | None = None

    def set_organization(self, organization_id: int):
        self.organization_id = organization_id

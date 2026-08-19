"""organization model added

Revision ID: fc0026e42b27
Revises: 4c49c8748086
Create Date: 2026-07-09 13:30:07.757324

"""

from typing import Sequence, Union

from migrations.base import BaseMigration

revision: str = "fc0026e42b27"
down_revision: Union[str, Sequence[str], None] = "4c49c8748086"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class OrganizationModelMigration(BaseMigration):
    table_name = "org_organizations"

    def __init__(self):
        super().__init__(
            revision="fc0026e42b27",
            down_revision="4c49c8748086",
        )
        self.create_whole_table = True

        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()

        self.string("name", length=255, nullable=False)
        self.string("website_url", length=500, nullable=True)
        self.string("org_size", length=100, nullable=True)
        self.string("monthly_email_volume", length=100, nullable=True, index=True)
        self.string("domain_email", length=255, nullable=True)
        self.string("org_logo", length=500, nullable=True)
        self.text("description", nullable=True)

        self.string("industry_sector", length=50, nullable=True, index=True)
        self.string("source", length=50, nullable=True, index=True)
        self.string("theme", length=20, nullable=False, default="light")
        self.string("timezone", length=100, nullable=True, default="UTC", index=True)
        self.string("status", length=50, nullable=False, default="active", index=True)

        self.foreign(
            "owner_id",
            "sys_auth_users",
            ondelete="RESTRICT",
            nullable=False,
            index=True,
        )

        self.date_time("deletion_requested_at", nullable=True)

        self.foreign(
            "deletion_requested_by_id",
            "sys_auth_users",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )

        self.date_time("scheduled_deletion_at", nullable=True, index=True)


def upgrade() -> None:
    """
    Function to create table.
    """
    OrganizationModelMigration().upgrade()


def downgrade() -> None:
    """
    Function to drop table.
    """
    OrganizationModelMigration().downgrade()
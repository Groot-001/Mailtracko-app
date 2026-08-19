"""organization activity model added

Revision ID: 61bd8e4674cc
Revises: 9aa8ad93d68e
Create Date: 2026-07-20

"""

from typing import Sequence, Union

from migrations.base import BaseMigration

revision: str = "61bd8e4674cc"
down_revision: Union[str, Sequence[str], None] = "859975d46996"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class OrganizationActivityModelMigration(BaseMigration):
    table_name = "org_organization_activities"

    def __init__(self):
        super().__init__(
            revision=revision,
            down_revision="859975d46996",
        )
        self.create_whole_table = True

        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()

        self.foreign(
            "organization_id",
            "org_organizations",
            ondelete="CASCADE",
            nullable=False,
            index=True,
        )

        self.string("activity_type", length=80, nullable=False, index=True)
        self.string("title", length=255, nullable=False)

        self.foreign(
            "actor_user_id",
            "sys_auth_users",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )

        self.foreign(
            "target_user_id",
            "sys_auth_users",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )

        self.string("target_email", length=255, nullable=True, index=True)


def upgrade() -> None:
    """
    Function to create table.
    """
    OrganizationActivityModelMigration().upgrade()


def downgrade() -> None:
    """
    Function to drop table.
    """
    OrganizationActivityModelMigration().downgrade()
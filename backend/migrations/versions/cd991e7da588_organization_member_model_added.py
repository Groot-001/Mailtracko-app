"""organization member model added

Revision ID: cd991e7da588
Revises: fc0026e42b27
Create Date: 2026-07-09 13:33:43.888138

"""

from typing import Sequence, Union

from migrations.base import BaseMigration

revision: str = "cd991e7da588"
down_revision: Union[str, Sequence[str], None] = "fc0026e42b27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class OrganizationMemberModelMigration(BaseMigration):
    table_name = "org_organization_members"

    def __init__(self):
        super().__init__(
            revision="cd991e7da588",
            down_revision="fc0026e42b27",
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
        self.foreign(
            "user_id",
            "sys_auth_users",
            ondelete="CASCADE",
            nullable=False,
            unique=True,
            index=True,
        )

        self.string("role_code", length=50, nullable=False, index=True)
        self.string("status", length=50, nullable=False, default="active", index=True)

        self.foreign(
            "invited_by_id",
            "sys_auth_users",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )

        self.date_time("joined_at", nullable=True, default=None)


def upgrade() -> None:
    """
    Function to create table.
    """
    OrganizationMemberModelMigration().upgrade()


def downgrade() -> None:
    """
    Function to drop table.
    """
    OrganizationMemberModelMigration().downgrade()
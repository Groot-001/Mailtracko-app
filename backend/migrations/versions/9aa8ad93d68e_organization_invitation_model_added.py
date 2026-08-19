"""organization invitation model added

Revision ID: 9aa8ad93d68e
Revises: cd991e7da588
Create Date: 2026-07-09 13:50:40.192080

"""

from typing import Sequence, Union

from migrations.base import BaseMigration

revision: str = "9aa8ad93d68e"
down_revision: Union[str, Sequence[str], None] = "cd991e7da588"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class OrganizationInvitationModelMigration(BaseMigration):
    table_name = "org_organization_invitations"

    def __init__(self):
        super().__init__(
            revision="9aa8ad93d68e",
            down_revision="cd991e7da588",
        )
        self.create_whole_table = True

        self.base_columns()
        self.audit_mixin_columns()

        self.foreign(
            "organization_id",
            "org_organizations",
            ondelete="CASCADE",
            nullable=False,
            index=True,
        )

        self.string("email", length=255, nullable=False, index=True)
        self.string("role_code", length=50, nullable=False, index=True)
        self.string("token_hash", length=255, nullable=False, unique=True, index=True)
        self.string("status", length=50, nullable=False, default="pending", index=True)

        self.foreign(
            "invited_by_id",
            "sys_auth_users",
            ondelete="RESTRICT",
            nullable=False,
            index=True,
        )

        self.date_time("expires_at", nullable=False, index=True)
        self.date_time("accepted_at", nullable=True, default=None)
        self.date_time("declined_at", nullable=True, default=None)
        self.date_time("revoked_at", nullable=True, default=None)


def upgrade() -> None:
    """
    Function to create table.
    """
    OrganizationInvitationModelMigration().upgrade()


def downgrade() -> None:
    """
    Function to drop table.
    """
    OrganizationInvitationModelMigration().downgrade()
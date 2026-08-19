"""User model added

Revision ID: cbb7e89b72cb
Revises:
Create Date: 2026-07-09 08:50:10.666796

"""


from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = "cbb7e89b72cb"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class UserModelMigration(BaseMigration):
    table_name = "sys_auth_users"

    def __init__(self):
        super().__init__(revision="cbb7e89b72cb", down_revision=None)
        self.create_whole_table = True
        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()

        self.string("full_name", length=255, nullable=False, default="")
        self.string("email", length=255, nullable=False, unique=True, index=True)
        self.string("profile_image", length=500, nullable=True)
        self.string("timezone", length=100, nullable=True)
        self.string("phone", length=50, nullable=True)
        self.string("country_code", length=10, nullable=True)
        self.string("location", length=255, nullable=True)
        self.string("theme", length=10, nullable=False, default="light")
        self.boolean("is_active", nullable=False, default=True)
        self.date_time("last_login_at", nullable=True)
        self.date_time("scheduled_deletion_at", nullable=True, default=None)
        self.date_time("email_verified_at", nullable=True, default=None)


def upgrade() -> None:
    UserModelMigration().upgrade()


def downgrade() -> None:
    UserModelMigration().downgrade()

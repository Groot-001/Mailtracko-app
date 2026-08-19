"""user_totp_secret_model_added

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-29 08:45:00.000000

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class UserTotpSecretMigration(BaseMigration):

    table_name = "auth_user_totp_secrets"

    def __init__(self):
        super().__init__(revision="b2c3d4e5f6a7", down_revision="a1b2c3d4e5f6")
        self.create_whole_table = True

        self.base_columns()
        self.foreign("user_id", "sys_auth_users", ondelete="CASCADE", nullable=False, unique=True)
        self.string("secret", length=255, nullable=False)
        self.boolean("enabled", nullable=False, default=False)


def upgrade() -> None:
    UserTotpSecretMigration().upgrade()


def downgrade() -> None:
    UserTotpSecretMigration().downgrade()

"""user_totp_recovery_code_model_added

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-07-29 08:45:00.000000

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class UserTotpRecoveryCodeMigration(BaseMigration):

    table_name = "auth_user_totp_recovery_codes"

    def __init__(self):
        super().__init__(revision="d4e5f6a7b8c9", down_revision="b2c3d4e5f6a7")
        self.create_whole_table = True

        self.base_columns()
        self.foreign("user_id", "sys_auth_users", ondelete="CASCADE", nullable=False, index=True)
        self.string("code_hash", length=128, nullable=False)
        self.date_time("used_at", nullable=True)


def upgrade() -> None:
    UserTotpRecoveryCodeMigration().upgrade()


def downgrade() -> None:
    UserTotpRecoveryCodeMigration().downgrade()

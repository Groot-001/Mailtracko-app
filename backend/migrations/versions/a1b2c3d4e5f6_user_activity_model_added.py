"""user_activity_model_added

Revision ID: a1b2c3d4e5f6
Revises: 663f5b4da534
Create Date: 2026-07-29 08:30:00.000000

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "663f5b4da534"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class UserActivityMigration(BaseMigration):

    table_name = "auth_user_activities"

    def __init__(self):
        super().__init__(revision="a1b2c3d4e5f6", down_revision="663f5b4da534")
        self.create_whole_table = True

        self.base_columns()
        self.foreign("user_id", "sys_auth_users", ondelete="CASCADE", nullable=False, index=True)
        self.string("activity_type", length=100, nullable=False, index=True)
        self.text("description", nullable=True)
        self.json("metadata", nullable=True)


def upgrade() -> None:
    UserActivityMigration().upgrade()


def downgrade() -> None:
    UserActivityMigration().downgrade()

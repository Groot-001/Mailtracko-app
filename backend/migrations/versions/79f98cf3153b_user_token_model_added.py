"""user_token_model_added

Revision ID: 79f98cf3153b
Revises: fda462ee7854
Create Date: 2026-07-09 10:05:50.691619

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '79f98cf3153b'
down_revision: Union[str, Sequence[str], None] = 'fda462ee7854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class UserTokenMigration(BaseMigration):

    table_name = "sys_auth_user_tokens"
    def __init__(self):
        super().__init__(revision='79f98cf3153b',down_revision='fda462ee7854')
        self.create_whole_table=True
        #describe your schemas here
        self.base_columns()
        self.audit_mixin_columns()

        self.foreign(
            "user_id", "sys_auth_users", ondelete="cascade", nullable=False, index=True
        )
        self.string("type", length=50, nullable=False, index=True)
        self.string("token_hash", length=255, nullable=False, index=True)
        self.date_time("expires_at", nullable=False)
        self.date_time("used_at", nullable=True)


def upgrade() -> None:
  """
  Function to create a table
  """
  UserTokenMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  UserTokenMigration().downgrade()

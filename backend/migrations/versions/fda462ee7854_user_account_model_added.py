"""user_account_model_added

Revision ID: fda462ee7854
Revises: cbb7e89b72cb
Create Date: 2026-07-09 09:58:26.226890

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = 'fda462ee7854'
down_revision: Union[str, Sequence[str], None] = 'cbb7e89b72cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class UserAccountMigration(BaseMigration):

    table_name = "sys_auth_user_accounts"
    def __init__(self):
        super().__init__(revision='fda462ee7854',down_revision='cbb7e89b72cb')
        self.create_whole_table=True
        #describe your schemas here
        self.base_columns()

        self.foreign("user_id", "sys_auth_users", ondelete="CASCADE", nullable=False, index=True)
        self.string("hashed_password", nullable=True, default=None)
        self.string('type', length=100, nullable=False)
        self.string("provider", nullable=True, default=None)
        self.string("provider_account_id", length=255, nullable=True, default=None)
        self.date_time("last_password_updated_at", nullable=True, default=None)


def upgrade() -> None:
  """
  Function to create a table
  """
  UserAccountMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  UserAccountMigration().downgrade()

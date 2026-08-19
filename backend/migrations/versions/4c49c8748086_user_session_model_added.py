"""user_session_model_added

Revision ID: 4c49c8748086
Revises: 79f98cf3153b
Create Date: 2026-07-09 10:14:14.830936

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '4c49c8748086'
down_revision: Union[str, Sequence[str], None] = '79f98cf3153b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class UserSessionMigration(BaseMigration):

    table_name = "sys_auth_user_sessions"
    def __init__(self):
        super().__init__(revision='4c49c8748086',down_revision='79f98cf3153b')
        self.create_whole_table=True
        #describe your schemas here
        self.base_columns()
        self.audit_mixin_columns()

        self.foreign(
            "user_id", "sys_auth_users", ondelete="cascade", nullable=False, index=True
        )
        self.date_time("expires_at", nullable=False)
        self.string("ip_address", length=45, nullable=True)
        self.string("user_agent", length=500, nullable=True)
        self.date_time("revoked_at", nullable=True)


def upgrade() -> None:
  """
  Function to create a table
  """
  UserSessionMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  UserSessionMigration().downgrade()

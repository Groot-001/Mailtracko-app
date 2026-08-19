"""email_oauth_configs_model_added

Revision ID: 1edd43517824
Revises: ccc61fb50c74
Create Date: 2026-07-17 11:54:47.738578

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '1edd43517824'
down_revision: Union[str, Sequence[str], None] = 'ccc61fb50c74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class OauthConfigMigration(BaseMigration):

    table_name = "email_oauth_configs"
    def __init__(self):
        super().__init__(revision='1edd43517824',down_revision='ccc61fb50c74')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.text("encrypted_refresh_token", nullable=False)


def upgrade() -> None:
  """
  Function to create a table
  """
  OauthConfigMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  OauthConfigMigration().downgrade()

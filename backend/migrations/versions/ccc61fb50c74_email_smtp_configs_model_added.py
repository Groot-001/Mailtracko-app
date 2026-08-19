"""email_smtp_configs_model_added

Revision ID: ccc61fb50c74
Revises: 9aa8ad93d68e
Create Date: 2026-07-17 11:53:33.005932

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = 'ccc61fb50c74'
down_revision: Union[str, Sequence[str], None] = '9aa8ad93d68e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class SmtpConfigMigration(BaseMigration):

    table_name = "email_smtp_configs"
    def __init__(self):
        super().__init__(revision='ccc61fb50c74',down_revision='9aa8ad93d68e')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.text("encrypted_password", nullable=False)
        self.string("smtp_host", length=255, nullable=False)
        self.integer("smtp_port", nullable=False)
        self.string("smtp_username", length=255, nullable=False)
        self.string("imap_host", length=255, nullable=True)
        self.integer("imap_port", nullable=True)
        self.string("verification_code_hash", length=255, nullable=True)
        self.date_time("verification_sent_at", nullable=True)
        self.integer("verification_attempts", nullable=False, default=0)
        self.date_time("code_expires_at", nullable=True)


def upgrade() -> None:
  """
  Function to create a table
  """
  SmtpConfigMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  SmtpConfigMigration().downgrade()

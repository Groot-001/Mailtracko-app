"""email_account_model_added

Revision ID: 859975d46996
Revises: 1edd43517824
Create Date: 2026-07-17 11:55:55.100576

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '859975d46996'
down_revision: Union[str, Sequence[str], None] = '1edd43517824'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class EmailAccountMigration(BaseMigration):

    table_name = "email_accounts"
    def __init__(self):
        super().__init__(revision='859975d46996',down_revision='1edd43517824')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()
        self.foreign("organization_id", "org_organizations", ondelete="CASCADE", nullable=False, index=True)
        self.string("provider", length=255, nullable=False, index=True)
        self.string("email", length=255, nullable=False)
        self.string("sender_name", length=255, nullable=True)
        self.string("status", length=50, nullable=False, default="pending_verification")
        self.foreign("smtp_config_id", "email_smtp_configs", ondelete="SET NULL", nullable=True)
        self.foreign("oauth_config_id", "email_oauth_configs", ondelete="SET NULL", nullable=True)
        self.string("health_status", length=50, nullable=False, default="unknown")
        self.integer("daily_sent_count", nullable=False, default=0)
        self.date("last_sent_date", nullable=True)
        self.integer("sending_limit", nullable=False, default=100)
        self.string("reply_to", length=255, nullable=True)
        self.text("signature", nullable=True)
        self.date_time("last_used_at", nullable=True)
        self.integer("health_score", nullable=True, comment="Overall health score 0-100")
        self.json("health_details", nullable=True, comment="Detailed health check breakdown")
        self.unique_constraint("organization_id", "email", name="uq_email_org_email")


def upgrade() -> None:
  """
  Function to create a table
  """
  EmailAccountMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  EmailAccountMigration().downgrade()

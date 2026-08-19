"""contact_activity_model_added

Revision ID: 77e3f5fec722
Revises: 54a7d98a2ca6
Create Date: 2026-07-24 10:43:55.860266

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '77e3f5fec722'
down_revision: Union[str, Sequence[str], None] = '54a7d98a2ca6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class ContactActivityMigration(BaseMigration):

    table_name = "contact_activities"
    def __init__(self):
        super().__init__(revision='77e3f5fec722',down_revision='54a7d98a2ca6')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.foreign("organization_id", "org_organizations", ondelete="CASCADE", nullable=False, index=True)
        self.foreign("contact_id", "contact_contacts", ondelete="CASCADE", nullable=False, index=True)
        self.string("activity_type", length=255, nullable=False, index=True)
        self.text("description", nullable=True)
        self.json("metadata", nullable=True)


def upgrade() -> None:
  """
  Function to create a table
  """
  ContactActivityMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  ContactActivityMigration().downgrade()

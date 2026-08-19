"""contact_model_added

Revision ID: 54a7d98a2ca6
Revises: 02e0e93197ef
Create Date: 2026-07-24 10:38:34.433324

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '54a7d98a2ca6'
down_revision: Union[str, Sequence[str], None] = '02e0e93197ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class ContactMigration(BaseMigration):

    table_name = "contact_contacts"
    def __init__(self):
        super().__init__(revision='54a7d98a2ca6',down_revision='02e0e93197ef')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.foreign("organization_id", "org_organizations", ondelete="CASCADE", nullable=False, index=True)
        self.foreign("contact_list_id", "contact_lists", ondelete="CASCADE", nullable=False, index=True)
        self.string("email", length=255, nullable=False, index=True)
        self.json("metadata", nullable=True)
        self.boolean("subscribed", default=True, nullable=False, index=True)
        self.date_time("unsubscribed_at", nullable=True)
        self.date_time("last_contacted_at", nullable=True)
        self.unique_constraint("contact_list_id", "email", name="uq_contact_list_email")


def upgrade() -> None:
  """
  Function to create a table
  """
  ContactMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  ContactMigration().downgrade()

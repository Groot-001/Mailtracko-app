"""contact_list_model_added

Revision ID: 02e0e93197ef
Revises: cfc25227cc8b
Create Date: 2026-07-24 10:18:58.511263

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '02e0e93197ef'
down_revision: Union[str, Sequence[str], None] = 'cfc25227cc8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class ContactListMigration(BaseMigration):

    table_name = "contact_lists"
    def __init__(self):
        super().__init__(revision='02e0e93197ef',down_revision='cfc25227cc8b')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()
        self.foreign("organization_id", "org_organizations", ondelete="CASCADE", nullable=False, index=True)
        self.string("name", length=255, nullable=False, index=True)
        self.text("description", nullable=True)
        self.json("field_definitions", nullable=True)
        self.unique_constraint("organization_id", "name", name="uq_contact_lists_org_name")


def upgrade() -> None:
  """
  Function to create a table
  """
  ContactListMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  ContactListMigration().downgrade()

"""contact_import_logs_model_added

Revision ID: 663f5b4da534
Revises: 77e3f5fec722
Create Date: 2026-07-24 11:49:45.839721

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = '663f5b4da534'
down_revision: Union[str, Sequence[str], None] = '77e3f5fec722'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class ContactImportLogMigration(BaseMigration):

    table_name = "contact_import_logs"
    def __init__(self):
        super().__init__(revision='663f5b4da534',down_revision='77e3f5fec722')
        self.create_whole_table=True
        #describe your schemas here

        self.base_columns()
        self.audit_mixin_columns()
        self.foreign("organization_id", "org_organizations", ondelete="CASCADE", nullable=False, index=True)
        self.foreign("contact_list_id", "contact_lists", ondelete="CASCADE", nullable=True)
        self.string("filename", length=500, nullable=False)
        self.json("column_mapping", nullable=True)
        self.integer("total_rows", nullable=False, default=0)
        self.integer("success_count", nullable=False, default=0)
        self.integer("error_count", nullable=False, default=0)
        self.json("errors", nullable=True)
        self.string("status", length=50, nullable=False, default="pending", index=True)


def upgrade() -> None:
  """
  Function to create a table
  """
  ContactImportLogMigration().upgrade()
  

def downgrade() -> None:
  """
  Function to drop a table
  """
  ContactImportLogMigration().downgrade()

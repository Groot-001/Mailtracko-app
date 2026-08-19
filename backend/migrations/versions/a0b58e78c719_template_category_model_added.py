"""template category model added

Revision ID: a0b58e78c719
Revises: 61bd8e4674cc
Create Date: 2026-07-21 10:00:05.268586

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = 'a0b58e78c719'
down_revision: Union[str, Sequence[str], None] = '61bd8e4674cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class TemplateCategoryModelMigration(BaseMigration):
    table_name = "template_categories"

    def __init__(self):
        super().__init__(
            revision="a0b58e78c719",
            down_revision="61bd8e4674cc",
        )
        self.create_whole_table = True

        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()

        self.string(
            "name",
            length=100,
            nullable=False,
        )

        self.text(
            "description",
            nullable=True,
        )

        self.integer(
            "display_order",
            nullable=False,
            default=0,
            index=True,
        )

        self.boolean(
            "is_active",
            nullable=False,
            default=True,
            index=True,
        )


def upgrade() -> None:
    """
    Function to create table.
    """
    TemplateCategoryModelMigration().upgrade()


def downgrade() -> None:
    """
    Function to drop table.
    """
    TemplateCategoryModelMigration().downgrade()
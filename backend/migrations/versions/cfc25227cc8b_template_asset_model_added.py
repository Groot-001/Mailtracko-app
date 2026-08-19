"""template asset model added

Revision ID: cfc25227cc8b
Revises: 032161b0aef0
Create Date: 2026-07-22 07:47:45.435998

"""

from migrations.base import BaseMigration
from typing import Sequence, Union

revision: str = 'cfc25227cc8b'
down_revision: Union[str, Sequence[str], None] = '032161b0aef0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

class TemplateAssetModelMigration(BaseMigration):
    table_name = "template_assets"

    def __init__(self):
        super().__init__(
            revision="cfc25227cc8b",
            down_revision="032161b0aef0",
        )
        self.create_whole_table = True

        self.base_columns()
        self.soft_delete_mixin_column()

        self.foreign(
            "template_id",
            "templates",
            ondelete="CASCADE",
            nullable=False,
            index=True,
        )

        self.foreign(
            "organization_id",
            "org_organizations",
            ondelete="CASCADE",
            nullable=True,
            index=True,
        )

        self.string(
            "original_filename",
            length=255,
            nullable=False,
        )

        self.string(
            "storage_key",
            length=500,
            nullable=False,
            unique=True,
            index=True,
        )

        self.text(
            "file_url",
            nullable=False,
        )

        self.string(
            "content_type",
            length=150,
            nullable=False,
        )

        self.biginteger(
            "file_size",
            nullable=False,
        )

        self.string(
            "asset_type",
            length=50,
            nullable=False,
            index=True,
        )

        self.string(
            "usage",
            length=50,
            nullable=False,
            index=True,
        )

        self.boolean(
            "is_active",
            nullable=False,
            default=True,
        )

        self.foreign(
            "uploaded_by_id",
            "sys_auth_users",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )


def upgrade() -> None:
    """
    Function to create table.
    """
    TemplateAssetModelMigration().upgrade()


def downgrade() -> None:
    """
    Function to drop table.
    """
    TemplateAssetModelMigration().downgrade()
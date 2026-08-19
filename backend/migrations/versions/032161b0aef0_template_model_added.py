"""template model added

Revision ID: 032161b0aef0
Revises: a0b58e78c719
Create Date: 2026-07-22 07:44:34.315157

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from migrations.base import BaseMigration


revision: str = "032161b0aef0"
down_revision: Union[str, Sequence[str], None] = "a0b58e78c719"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class TemplateModelMigration(BaseMigration):
    """
    Migration for creating the templates table.
    """

    table_name = "templates"

    def __init__(self):
        super().__init__(
            revision='032161b0aef0',
            down_revision='a0b58e78c719',
        )

        self.create_whole_table = True

        self.base_columns()
        self.audit_mixin_columns()
        self.soft_delete_mixin_column()

        self.foreign(
            "organization_id",
            "org_organizations",
            ondelete="CASCADE",
            nullable=True,
            index=True,
        )

        self.foreign(
            "category_id",
            "template_categories",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )

        self.foreign(
            "source_template_id",
            "templates",
            ondelete="SET NULL",
            nullable=True,
            index=True,
        )

        self.string(
            "name",
            length=150,
            nullable=False,
        )

        self.text(
            "description",
            nullable=True,
            default=None,
        )

        self.string(
            "subject",
            length=255,
            nullable=False,
        )

        self.string(
            "preheader",
            length=255,
            nullable=True,
            default=None,
        )

        self.text(
            "body_html",
            nullable=False,
        )

        self.string(
            "from_name",
            length=150,
            nullable=True,
            default=None,
        )

        self.string(
            "from_email",
            length=320,
            nullable=True,
            default=None,
        )

        self.fields.append(
            sa.Column(
                "tags",
                JSONB(),
                nullable=False,
                default=list,
                server_default=sa.text("'[]'::jsonb"),
            )
        )

        self.string(
            "template_type",
            length=50,
            nullable=False,
            default="custom",
            server_default="custom",
            index=True,
        )

        self.string(
            "status",
            length=50,
            nullable=False,
            default="draft",
            server_default="draft",
            index=True,
        )

        self.boolean(
            "is_active",
            nullable=False,
            default=True,
            server_default=sa.true(),
            index=True,
        )

        self.boolean(
            "is_default",
            nullable=False,
            default=False,
            server_default=sa.false(),
            index=True,
        )

        self.boolean(
            "smart_personalization_enabled",
            nullable=False,
            default=False,
            server_default=sa.false(),
        )

        self.date_time(
            "published_at",
            nullable=True,
            default=None,
        )

        self.date_time(
            "archived_at",
            nullable=True,
            default=None,
        )


def upgrade() -> None:
    """
    Creates the templates table and its indexes.
    """
    TemplateModelMigration().upgrade()

    op.create_index(
        "ix_templates_organization_status",
        "templates",
        [
            "organization_id",
            "status",
        ],
    )

    op.create_index(
        "ix_templates_organization_deleted_at",
        "templates",
        [
            "organization_id",
            "deleted_at",
        ],
    )

    op.create_index(
        "ix_templates_organization_default",
        "templates",
        [
            "organization_id",
            "is_default",
        ],
    )

    op.create_index(
        "ix_templates_type_category",
        "templates",
        [
            "template_type",
            "category_id",
        ],
    )

    op.create_index(
        "ix_templates_updated_at",
        "templates",
        [
            "updated_at",
        ],
    )

    op.create_index(
        "ix_templates_created_at",
        "templates",
        [
            "created_at",
        ],
    )

    op.create_index(
        "uq_templates_one_default_per_organization",
        "templates",
        [
            "organization_id",
        ],
        unique=True,
        postgresql_where=sa.text(
            "is_default IS TRUE "
            "AND template_type = 'custom' "
            "AND deleted_at IS NULL"
        ),
    )


def downgrade() -> None:
    """
    Drops the templates table.
    """
    TemplateModelMigration().downgrade()
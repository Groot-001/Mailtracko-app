"""scope custom template categories to organizations

Revision ID: f8b9c0d1e2f3
Revises: c0d1e2f3a4b5
Create Date: 2026-08-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from migrations.base import BaseMigration

revision: str = "f8b9c0d1e2f3"
down_revision: str | Sequence[str] | None = "c0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class TemplateCategoryOrganizationScopeMigration(BaseMigration):
    """Add optional organization ownership to template categories."""

    table_name = "template_categories"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="c0d1e2f3a4b5")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "organization_id",
                sa.Integer(),
                sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                nullable=True,
            )
        )


def upgrade() -> None:
    TemplateCategoryOrganizationScopeMigration().upgrade()
    op.create_index(
        "ix_template_categories_organization_id",
        "template_categories",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "uq_template_categories_org_name",
        "template_categories",
        ["organization_id", "name"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_template_categories_org_name",
        table_name="template_categories",
    )
    op.drop_index(
        "ix_template_categories_organization_id",
        table_name="template_categories",
    )
    TemplateCategoryOrganizationScopeMigration().downgrade()

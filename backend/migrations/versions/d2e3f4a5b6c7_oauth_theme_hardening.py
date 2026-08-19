"""persist Google Sheets OAuth ownership and normalize workspace themes

Revision ID: d2e3f4a5b6c7
Revises: d1e2f3a4b5c6
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: str | Sequence[str] | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_oauth_configs",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "email_oauth_configs",
        sa.Column("purpose", sa.String(length=50), nullable=True),
    )
    op.create_index(
        "ix_email_oauth_configs_organization_purpose",
        "email_oauth_configs",
        ["organization_id", "purpose"],
    )
    op.create_unique_constraint(
        "uq_email_oauth_configs_organization_purpose",
        "email_oauth_configs",
        ["organization_id", "purpose"],
    )

    # The product now has exactly two supported workspace themes. Preserve the
    # intent of existing records while removing stale frontend-only variants.
    op.execute(
        """
        UPDATE org_organizations
        SET theme = CASE
            WHEN theme = 'midnight-focus' THEN 'dark'
            ELSE 'light'
        END
        WHERE theme NOT IN ('light', 'dark')
        """
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_email_oauth_configs_organization_purpose",
        "email_oauth_configs",
        type_="unique",
    )
    op.drop_index(
        "ix_email_oauth_configs_organization_purpose",
        table_name="email_oauth_configs",
    )
    op.drop_column("email_oauth_configs", "purpose")
    op.drop_column("email_oauth_configs", "organization_id")

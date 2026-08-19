"""campaign A/B test holdout continuation

Revision ID: f7a8b9c0d1e2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from migrations.base import BaseMigration

revision: str = "f7a8b9c0d1e2"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class CampaignRecipientABSampleMigration(BaseMigration):
    """Add/drop the explicit A/B sampling flag using the project migration convention."""

    table_name = "campaign_recipients"

    def __init__(self) -> None:
        super().__init__(revision=revision, down_revision="f6a7b8c9d0e1")
        self.create_whole_table = False
        self.add_column(
            sa.Column(
                "ab_test_sampled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )


def upgrade() -> None:
    # Existing recipients were already assigned and sent using the previous flow,
    # so the default preserves them as test-sampled while new holdouts are explicit.
    CampaignRecipientABSampleMigration().upgrade()
    op.create_index(
        "ix_campaign_recipients_campaign_ab_sample",
        "campaign_recipients",
        ["campaign_id", "ab_test_sampled", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_campaign_recipients_campaign_ab_sample",
        table_name="campaign_recipients",
    )
    CampaignRecipientABSampleMigration().downgrade()

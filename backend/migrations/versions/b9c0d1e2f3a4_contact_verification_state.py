"""contact verification and lifecycle state

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b9c0d1e2f3a4"
down_revision: str | Sequence[str] | None = "a8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "contact_contacts",
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
    )
    op.add_column(
        "contact_contacts",
        sa.Column(
            "verification_status",
            sa.String(30),
            nullable=False,
            server_default="unverified",
        ),
    )
    op.add_column(
        "contact_contacts", sa.Column("verification_sub_status", sa.String(80))
    )
    op.add_column("contact_contacts", sa.Column("verification_score", sa.Integer()))
    op.add_column("contact_contacts", sa.Column("verification_details", sa.JSON()))
    op.add_column(
        "contact_contacts", sa.Column("verified_at", sa.DateTime(timezone=True))
    )
    op.add_column("contact_contacts", sa.Column("bounce_risk", sa.String(20)))
    op.add_column(
        "contact_contacts", sa.Column("last_bounced_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "contact_contacts", sa.Column("archived_at", sa.DateTime(timezone=True))
    )
    op.create_index("ix_contact_contacts_status", "contact_contacts", ["status"])
    op.create_index(
        "ix_contact_contacts_verification_status",
        "contact_contacts",
        ["verification_status"],
    )
    op.create_index(
        "ix_contact_contacts_bounce_risk", "contact_contacts", ["bounce_risk"]
    )


def downgrade() -> None:
    op.drop_index("ix_contact_contacts_bounce_risk", table_name="contact_contacts")
    op.drop_index(
        "ix_contact_contacts_verification_status", table_name="contact_contacts"
    )
    op.drop_index("ix_contact_contacts_status", table_name="contact_contacts")
    for column in (
        "archived_at",
        "last_bounced_at",
        "bounce_risk",
        "verified_at",
        "verification_details",
        "verification_score",
        "verification_sub_status",
        "verification_status",
        "status",
    ):
        op.drop_column("contact_contacts", column)

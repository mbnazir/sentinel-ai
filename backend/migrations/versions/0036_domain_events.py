"""domain events

Revision ID: 0036_domain_events
Revises: 0032_job_schedules
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0036_domain_events"
down_revision: str | None = "0032_job_schedules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_id", sa.String(100), nullable=False, unique=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("causation_id", sa.String(100), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_domain_events_org_type", "domain_events", ["organization_id", "event_type"])
    op.create_index("ix_domain_events_correlation", "domain_events", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_domain_events_correlation", table_name="domain_events")
    op.drop_index("ix_domain_events_org_type", table_name="domain_events")
    op.drop_table("domain_events")

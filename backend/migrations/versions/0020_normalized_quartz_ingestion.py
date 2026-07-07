"""normalized quartz ingestion stores

Revision ID: 0020_normalized_quartz_ingestion
Revises: 0017_users_and_sso
Create Date: 2026-07-06
"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0020_normalized_quartz_ingestion"
down_revision: str | None = "0017_users_and_sso"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "normalized_login_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("agent_external_id", sa.String(100), nullable=True),
        sa.Column("supervisor_external_id", sa.String(100), nullable=True),
        sa.Column("shift_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(100), nullable=True),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_normalized_session_org_external"),
    )
    op.create_index("ix_normalized_sessions_shift_date", "normalized_login_sessions", ["shift_date"])
    op.create_index("ix_normalized_sessions_agent", "normalized_login_sessions", ["agent_external_id"])

    op.create_table(
        "normalized_activities",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("connector_type", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=False),
        sa.Column("login_session_external_id", sa.String(100), nullable=False),
        sa.Column("agent_external_id", sa.String(100), nullable=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("activity_type", sa.String(255), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.UniqueConstraint("organization_id", "external_id", name="uq_normalized_activity_org_external"),
    )
    op.create_index("ix_normalized_activities_session", "normalized_activities", ["login_session_external_id"])
    op.create_index("ix_normalized_activities_source", "normalized_activities", ["source"])


def downgrade() -> None:
    op.drop_index("ix_normalized_activities_source", table_name="normalized_activities")
    op.drop_index("ix_normalized_activities_session", table_name="normalized_activities")
    op.drop_table("normalized_activities")
    op.drop_index("ix_normalized_sessions_agent", table_name="normalized_login_sessions")
    op.drop_index("ix_normalized_sessions_shift_date", table_name="normalized_login_sessions")
    op.drop_table("normalized_login_sessions")

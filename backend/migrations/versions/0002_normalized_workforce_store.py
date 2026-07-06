"""normalized workforce store

Revision ID: 0002_normalized
Revises: 0001_initial
Create Date: 2026-07-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_normalized"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_sources",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.BigInteger(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("connector_id", sa.BigInteger(), sa.ForeignKey("connectors.id"), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("connector_id", "entity_type", "external_id", name="uq_external_source_entity"),
    )

    op.create_table(
        "normalized_login_sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.BigInteger(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("connector_id", sa.BigInteger(), sa.ForeignKey("connectors.id"), nullable=False),
        sa.Column("connector_run_id", sa.BigInteger(), sa.ForeignKey("connector_runs.id"), nullable=True),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("agent_external_id", sa.String(length=100), nullable=True),
        sa.Column("supervisor_external_id", sa.String(length=100), nullable=True),
        sa.Column("shift_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("connector_id", "external_id", name="uq_normalized_session_external"),
    )
    op.create_index("ix_normalized_sessions_shift_date", "normalized_login_sessions", ["shift_date"])
    op.create_index("ix_normalized_sessions_agent_shift", "normalized_login_sessions", ["agent_external_id", "shift_date"])

    op.create_table(
        "normalized_activities",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.BigInteger(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("connector_id", sa.BigInteger(), sa.ForeignKey("connectors.id"), nullable=False),
        sa.Column("connector_run_id", sa.BigInteger(), sa.ForeignKey("connector_runs.id"), nullable=True),
        sa.Column("login_session_id", sa.BigInteger(), sa.ForeignKey("normalized_login_sessions.id"), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("login_session_external_id", sa.String(length=100), nullable=False),
        sa.Column("agent_external_id", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_code", sa.Integer(), nullable=True),
        sa.Column("activity_type", sa.String(length=100), nullable=False),
        sa.Column("activity_type_external_id", sa.String(length=100), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("inactivity_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("connector_id", "external_id", name="uq_normalized_activity_external"),
    )
    op.create_index("ix_normalized_activities_session", "normalized_activities", ["login_session_id"])
    op.create_index("ix_normalized_activities_source", "normalized_activities", ["source"])
    op.create_index("ix_normalized_activities_start", "normalized_activities", ["start_time"])


def downgrade() -> None:
    op.drop_index("ix_normalized_activities_start", table_name="normalized_activities")
    op.drop_index("ix_normalized_activities_source", table_name="normalized_activities")
    op.drop_index("ix_normalized_activities_session", table_name="normalized_activities")
    op.drop_table("normalized_activities")
    op.drop_index("ix_normalized_sessions_agent_shift", table_name="normalized_login_sessions")
    op.drop_index("ix_normalized_sessions_shift_date", table_name="normalized_login_sessions")
    op.drop_table("normalized_login_sessions")
    op.drop_table("external_sources")

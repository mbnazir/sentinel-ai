"""operational snapshot ledger"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_operational_snapshot_ledger"
down_revision: str | None = "0001_platform_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("connectors", sa.Column("base_url", sa.String(length=500), nullable=True))
    op.add_column(
        "connectors",
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("connector_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("connectors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("shift_date_from", sa.Date(), nullable=False),
        sa.Column("shift_date_to", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activity_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint("connector_id", "idempotency_key", name="uq_ingestion_connector_key"),
    )
    op.create_index("ix_ingestion_runs_shift_range", "ingestion_runs", ["shift_date_from", "shift_date_to"])

    op.create_table(
        "session_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("source_session_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("supervisor_id", sa.String(length=64), nullable=True),
        sa.Column("shift_date", sa.Date(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status_id", sa.Integer(), nullable=True),
        sa.Column("dispute_reason_id", sa.Integer(), nullable=True),
        sa.Column("dispute_state", sa.Integer(), nullable=True),
        sa.Column("supervisor_status_id", sa.Integer(), nullable=True),
        sa.Column("ready_for_payroll", sa.Boolean(), nullable=False),
        sa.Column("payroll_adjusted", sa.Boolean(), nullable=False),
        sa.Column("payroll_adjusted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_added_by", sa.String(length=64), nullable=True),
        sa.Column("add_session_reason_id", sa.Integer(), nullable=True),
        sa.Column("agent_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supervisor_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manager_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("multiple_logins", sa.Integer(), nullable=False),
        sa.Column("agent_ip", sa.String(length=255), nullable=True),
        sa.Column("machine_hostname", sa.String(length=255), nullable=True),
        sa.Column("primary_campaign_id", sa.String(length=200), nullable=True),
        sa.Column("primary_campaign_name", sa.String(length=200), nullable=True),
        sa.Column("primary_client_id", sa.Integer(), nullable=True),
        sa.Column("primary_client_name", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ingestion_run_id", "source_system", "source_session_id", name="uq_session_snapshot_run_source"),
    )
    op.create_index("ix_session_snapshots_agent_shift", "session_snapshots", ["agent_id", "shift_date"])
    op.create_index("ix_session_snapshots_source_session", "session_snapshots", ["source_system", "source_session_id"])

    op.create_table(
        "activity_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("source_activity_id", sa.String(length=64), nullable=False),
        sa.Column("source_session_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=True),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("activity_type_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.BigInteger(), nullable=True),
        sa.Column("inactivity_seconds", sa.BigInteger(), nullable=False),
        sa.Column("campaign_id", sa.String(length=64), nullable=True),
        sa.Column("campaign_name", sa.String(length=255), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("ingestion_run_id", "source_system", "source_activity_id", name="uq_activity_snapshot_run_source"),
    )
    op.create_index("ix_activity_snapshots_source_session", "activity_snapshots", ["source_system", "source_session_id"])
    op.create_index("ix_activity_snapshots_session_source", "activity_snapshots", ["source_session_id", "data_source_id"])
    op.create_index("ix_activity_snapshots_agent_start", "activity_snapshots", ["agent_id", "start_at"])


def downgrade() -> None:
    op.drop_table("activity_snapshots")
    op.drop_table("session_snapshots")
    op.drop_table("ingestion_runs")
    op.drop_column("connectors", "config_json")
    op.drop_column("connectors", "base_url")

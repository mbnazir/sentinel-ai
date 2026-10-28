"""durable resumable ingestion checkpoints

Revision ID: 0009_durable_ingestion_progress
Revises: 0008_ai_investigator
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_durable_ingestion_progress"
down_revision: str | None = "0008_ai_investigator"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_progress",
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("completion_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("reconciliation_status", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("session_cursor", sa.Text(), nullable=True),
        sa.Column("session_seen_cursors_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("session_page", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("session_collection_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expected_session_count", sa.Integer(), nullable=True),
        sa.Column("sessions_retrieved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_persisted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sessions_with_completed_activities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_activity_count", sa.Integer(), nullable=True),
        sa.Column("activities_retrieved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activities_persisted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_activity_batches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_count_mismatches_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("date_coverage_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("reconciliation_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_failure_category", sa.String(80), nullable=True),
        sa.Column("last_successful_checkpoint_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_token", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "ingestion_activity_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("batch_key", sa.String(64), nullable=False),
        sa.Column("session_ids_json", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("cursor", sa.Text(), nullable=True),
        sa.Column("seen_cursors_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("page_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expected_activity_count", sa.Integer(), nullable=True),
        sa.Column("activities_retrieved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activities_persisted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_category", sa.String(80), nullable=True),
        sa.Column("failure_code", sa.Integer(), nullable=True),
        sa.Column("safe_error_message", sa.String(500), nullable=True),
        sa.Column("last_successful_checkpoint_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("ingestion_run_id", "batch_key", name="uq_ingestion_batch_key"),
    )
    op.create_index("ix_ingestion_activity_batches_status", "ingestion_activity_batches",
                    ["ingestion_run_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_activity_batches_status", table_name="ingestion_activity_batches")
    op.drop_table("ingestion_activity_batches")
    op.drop_table("ingestion_progress")

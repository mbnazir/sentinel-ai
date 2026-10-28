"""audit explicit legacy ingestion recovery initialization

Revision ID: 0010_ingestion_recovery_audit
Revises: 0009_durable_ingestion_progress
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_ingestion_recovery_audit"
down_revision: str | None = "0009_durable_ingestion_progress"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ingestion_progress", sa.Column(
        "recovery_attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ingestion_progress", sa.Column(
        "recovery_initialized_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ingestion_progress", sa.Column(
        "recovery_initialized_by", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("ingestion_progress", "recovery_initialized_by")
    op.drop_column("ingestion_progress", "recovery_initialized_at")
    op.drop_column("ingestion_progress", "recovery_attempt_count")

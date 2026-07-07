"""normalized timeline activities

Revision ID: 0013_normalized_timeline_activities
Revises: 0010_investigation_persistence
Create Date: 2026-07-06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0013_normalized_timeline_activities"
down_revision: str | None = "0010_investigation_persistence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "normalized_timeline_activities",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("organization_id", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=100), nullable=False),
        sa.Column("login_session_external_id", sa.String(length=100), nullable=False),
        sa.Column("agent_external_id", sa.String(length=100), nullable=True),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("source_label", sa.String(length=50), nullable=False),
        sa.Column("activity_type_id", sa.Integer(), nullable=False),
        sa.Column("activity_type_label", sa.String(length=255), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("risk_type", sa.String(length=50), nullable=True),
        sa.Column("risk_note", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_normalized_timeline_session",
        "normalized_timeline_activities",
        ["login_session_external_id"],
    )
    op.create_index(
        "ix_normalized_timeline_external_id",
        "normalized_timeline_activities",
        ["external_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_normalized_timeline_external_id", table_name="normalized_timeline_activities")
    op.drop_index("ix_normalized_timeline_session", table_name="normalized_timeline_activities")
    op.drop_table("normalized_timeline_activities")

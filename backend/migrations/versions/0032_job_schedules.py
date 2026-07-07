"""job schedules

Revision ID: 0032_job_schedules
Revises: 0031_persistent_jobs
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0032_job_schedules"
down_revision: str | None = "0031_persistent_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_schedules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("schedule_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_job_schedules_due", "job_schedules", ["status", "next_run_at"])
    op.create_index("ix_job_schedules_org", "job_schedules", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_job_schedules_org", table_name="job_schedules")
    op.drop_index("ix_job_schedules_due", table_name="job_schedules")
    op.drop_table("job_schedules")

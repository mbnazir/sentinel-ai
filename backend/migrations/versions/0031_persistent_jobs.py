"""persistent jobs

Revision ID: 0031_persistent_jobs
Revises: 0026_persisted_anomaly_findings
Create Date: 2026-07-07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0031_persistent_jobs"
down_revision: str | None = "0026_persisted_anomaly_findings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("job_id", sa.String(100), nullable=False, unique=True),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("organization_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("requested_by", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_job_runs_org_status", "job_runs", ["organization_id", "status"])
    op.create_index("ix_job_runs_type", "job_runs", ["job_type"])


def downgrade() -> None:
    op.drop_index("ix_job_runs_type", table_name="job_runs")
    op.drop_index("ix_job_runs_org_status", table_name="job_runs")
    op.drop_table("job_runs")

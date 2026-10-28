"""Add explicit baseline provenance and QF-001 cross-scan idempotency.

Revision ID: 0012_qf001_comparison_scan_provenance
Revises: 0011_activity_revision_snapshot_identity
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_qf001_comparison_scan_provenance"
down_revision: str | None = "0011_activity_revision_snapshot_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "analysis_scans",
        sa.Column("baseline_ingestion_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "analysis_scans",
        sa.Column(
            "eligibility_mode", sa.String(length=32), nullable=False,
            server_default="STRICT_RECONCILED",
        ),
    )
    op.add_column(
        "analysis_scans", sa.Column("eligibility_override_reason", sa.Text(), nullable=True)
    )
    op.add_column(
        "analysis_scans",
        sa.Column("eligibility_override_role", sa.String(length=20), nullable=True),
    )
    op.create_foreign_key(
        "fk_analysis_scans_baseline_ingestion_run",
        "analysis_scans",
        "ingestion_runs",
        ["baseline_ingestion_run_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_analysis_scans_distinct_comparison_runs",
        "analysis_scans",
        "baseline_ingestion_run_id IS NULL OR baseline_ingestion_run_id <> ingestion_run_id",
    )
    op.create_check_constraint(
        "ck_analysis_scans_eligibility_mode",
        "analysis_scans",
        "eligibility_mode IN ('STRICT_RECONCILED', 'OBSERVED_RECORDS_ONLY')",
    )
    op.create_check_constraint(
        "ck_analysis_scans_observed_mode_authorized",
        "analysis_scans",
        "eligibility_mode <> 'OBSERVED_RECORDS_ONLY' OR "
        "(eligibility_override_reason IS NOT NULL AND length(trim(eligibility_override_reason)) >= 10 "
        "AND eligibility_override_role IN ('manager', 'admin'))",
    )
    op.create_check_constraint(
        "ck_analysis_scans_comparison_requires_baseline",
        "analysis_scans",
        "scope <> 'historical_comparison' OR baseline_ingestion_run_id IS NOT NULL",
    )
    op.create_index(
        "ix_analysis_scans_baseline_run", "analysis_scans", ["baseline_ingestion_run_id"]
    )
    op.create_index(
        "uq_durable_qf001_finding_key",
        "durable_findings",
        ["finding_key"],
        unique=True,
        postgresql_where=sa.text("rule_id = 'QF-001'"),
    )


def downgrade() -> None:
    op.drop_index("uq_durable_qf001_finding_key", table_name="durable_findings")
    op.drop_index("ix_analysis_scans_baseline_run", table_name="analysis_scans")
    op.drop_constraint("ck_analysis_scans_observed_mode_authorized", "analysis_scans", type_="check")
    op.drop_constraint("ck_analysis_scans_eligibility_mode", "analysis_scans", type_="check")
    op.drop_constraint("ck_analysis_scans_comparison_requires_baseline", "analysis_scans", type_="check")
    op.drop_constraint("ck_analysis_scans_distinct_comparison_runs", "analysis_scans", type_="check")
    op.drop_constraint(
        "fk_analysis_scans_baseline_ingestion_run", "analysis_scans", type_="foreignkey"
    )
    op.drop_column("analysis_scans", "baseline_ingestion_run_id")
    op.drop_column("analysis_scans", "eligibility_override_role")
    op.drop_column("analysis_scans", "eligibility_override_reason")
    op.drop_column("analysis_scans", "eligibility_mode")

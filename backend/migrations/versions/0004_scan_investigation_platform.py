"""scan and investigation platform

Revision ID: 0004_scan_investigation_platform
Revises: 0003_organizational_dimensions
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_scan_investigation_platform"
down_revision = "0003_organizational_dimensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("analysis_scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("date_from", sa.Date(), nullable=False),
        sa.Column("date_to", sa.Date(), nullable=False),
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column("scope", sa.String(40), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("employee_days_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("finding_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )
    op.create_index("ix_analysis_scans_ingestion_range","analysis_scans",["ingestion_run_id","date_from","date_to"])

    op.create_table("durable_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_scans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("finding_key", sa.String(180), nullable=False),
        sa.Column("agent_id", sa.String(64)),
        sa.Column("shift_date", sa.Date()),
        sa.Column("source_session_id", sa.String(64)),
        sa.Column("rule_id", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_contribution", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(), nullable=False),
        sa.Column("immutable_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("scan_id","finding_key",name="uq_durable_finding_scan_key"),
    )
    op.create_index("ix_durable_findings_agent_shift","durable_findings",["agent_id","shift_date"])
    op.create_index("ix_durable_findings_rule","durable_findings",["rule_id"])

    op.create_table("investigation_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_number", sa.String(40), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("disposition", sa.String(40), nullable=False),
        sa.Column("assigned_to", sa.String(128)),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_investigation_cases_status_assignee","investigation_cases",["status","assigned_to"])

    op.create_table("case_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigation_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("durable_findings.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("case_id","finding_id",name="uq_case_finding"),
    )

    op.create_table("investigation_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigation_cases.id", ondelete="RESTRICT")),
        sa.Column("scan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_scans.id", ondelete="RESTRICT")),
        sa.Column("actor", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("event_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_investigation_audit_case_created","investigation_audit_events",["case_id","created_at"])
    op.create_index("ix_investigation_audit_scan_created","investigation_audit_events",["scan_id","created_at"])


def downgrade() -> None:
    op.drop_table("investigation_audit_events")
    op.drop_table("case_findings")
    op.drop_table("investigation_cases")
    op.drop_table("durable_findings")
    op.drop_table("analysis_scans")

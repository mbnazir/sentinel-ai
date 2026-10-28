from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ConnectorModel(Base):
    __tablename__ = "connectors"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    config_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IngestionRunModel(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        UniqueConstraint("connector_id", "idempotency_key", name="uq_ingestion_connector_key"),
        Index("ix_ingestion_runs_shift_range", "shift_date_from", "shift_date_to"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    connector_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("connectors.id", ondelete="RESTRICT"), nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    shift_date_from: Mapped[date] = mapped_column(Date, nullable=False)
    shift_date_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class IngestionProgressModel(Base):
    __tablename__ = "ingestion_progress"

    ingestion_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), primary_key=True
    )
    completion_status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    reconciliation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    session_cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_seen_cursors_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    session_page: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    session_collection_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_session_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sessions_retrieved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_persisted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_with_completed_activities: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_activity_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activities_retrieved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_persisted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_activity_batches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_count_mismatches_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    date_coverage_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    reconciliation_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    last_failure_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_successful_checkpoint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lease_token: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recovery_initialized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_initialized_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IngestionActivityBatchModel(Base):
    __tablename__ = "ingestion_activity_batches"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "batch_key", name="uq_ingestion_batch_key"),
        Index("ix_ingestion_activity_batches_status", "ingestion_run_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False
    )
    batch_key: Mapped[str] = mapped_column(String(64), nullable=False)
    session_ids_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    seen_cursors_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_activity_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activities_retrieved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_persisted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_failure_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    safe_error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_successful_checkpoint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionSnapshotModel(Base):
    __tablename__ = "session_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ingestion_run_id", "source_system", "source_session_id", name="uq_session_snapshot_run_source"
        ),
        Index("ix_session_snapshots_agent_shift", "agent_id", "shift_date"),
        Index("ix_session_snapshots_source_session", "source_system", "source_session_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False
    )
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    source_session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    supervisor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manager_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    site_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    site_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dispute_reason_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dispute_state: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supervisor_status_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ready_for_payroll: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payroll_adjusted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payroll_adjusted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_added_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    add_session_reason_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    agent_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supervisor_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manager_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    multiple_logins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_ip: Mapped[str | None] = mapped_column(String(255), nullable=True)
    machine_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_campaign_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_campaign_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_client_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    primary_client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActivitySnapshotModel(Base):
    __tablename__ = "activity_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ingestion_run_id", "source_system", "source_session_id", "source_activity_id",
            "data_source_id", name="uq_activity_snapshot_run_session_revision"
        ),
        Index("ix_activity_snapshots_source_session", "source_system", "source_session_id"),
        Index("ix_activity_snapshots_session_source", "source_session_id", "data_source_id"),
        Index("ix_activity_snapshots_agent_start", "agent_id", "start_at"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False
    )
    source_system: Mapped[str] = mapped_column(String(50), nullable=False)
    source_activity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_source_id: Mapped[int] = mapped_column(Integer, nullable=False)
    activity_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    inactivity_seconds: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    campaign_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    campaign_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalysisScanModel(Base):
    __tablename__ = "analysis_scans"
    __table_args__ = (
        Index("ix_analysis_scans_ingestion_range", "ingestion_run_id", "date_from", "date_to"),
        Index("ix_analysis_scans_baseline_run", "baseline_ingestion_run_id"),
        CheckConstraint(
            "baseline_ingestion_run_id IS NULL OR baseline_ingestion_run_id <> ingestion_run_id",
            name="ck_analysis_scans_distinct_comparison_runs",
        ),
        CheckConstraint(
            "scope <> 'historical_comparison' OR baseline_ingestion_run_id IS NOT NULL",
            name="ck_analysis_scans_comparison_requires_baseline",
        ),
        CheckConstraint(
            "eligibility_mode IN ('STRICT_RECONCILED', 'OBSERVED_RECORDS_ONLY')",
            name="ck_analysis_scans_eligibility_mode",
        ),
        CheckConstraint(
            "eligibility_mode <> 'OBSERVED_RECORDS_ONLY' OR "
            "(eligibility_override_reason IS NOT NULL AND length(trim(eligibility_override_reason)) >= 10 "
            "AND eligibility_override_role IN ('manager', 'admin'))",
            name="ck_analysis_scans_observed_mode_authorized",
        ),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ingestion_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=False
    )
    baseline_ingestion_run_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("ingestion_runs.id", ondelete="RESTRICT"), nullable=True
    )
    eligibility_mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default="STRICT_RECONCILED",
        server_default="STRICT_RECONCILED",
    )
    eligibility_override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    eligibility_override_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(String(40), nullable=False, default="employee_day")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    employee_days_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rule_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    finalization_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    summary_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    dead_letter_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DurableFindingModel(Base):
    __tablename__ = "durable_findings"
    __table_args__ = (
        UniqueConstraint("scan_id", "finding_key", name="uq_durable_finding_scan_key"),
        Index("ix_durable_findings_agent_shift", "agent_id", "shift_date"),
        Index("ix_durable_findings_rule", "rule_id"),
        Index(
            "uq_durable_qf001_finding_key",
            "finding_key",
            unique=True,
            postgresql_where=text("rule_id = 'QF-001'"),
        ),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("analysis_scans.id", ondelete="RESTRICT"), nullable=False
    )
    finding_key: Mapped[str] = mapped_column(String(180), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shift_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_id: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    risk_contribution: Mapped[float] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    immutable_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvestigationCaseModel(Base):
    __tablename__ = "investigation_cases"
    __table_args__ = (
        UniqueConstraint("case_number", name="uq_investigation_case_number"),
        Index("ix_investigation_cases_status_assignee", "status", "assigned_to"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_number: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open")
    disposition: Mapped[str] = mapped_column(String(40), nullable=False, default="undetermined")
    assigned_to: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CaseFindingModel(Base):
    __tablename__ = "case_findings"
    __table_args__ = (
        UniqueConstraint("case_id", "finding_id", name="uq_case_finding"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("investigation_cases.id", ondelete="RESTRICT"), nullable=False
    )
    finding_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("durable_findings.id", ondelete="RESTRICT"), nullable=False
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvestigationAuditEventModel(Base):
    __tablename__ = "investigation_audit_events"
    __table_args__ = (
        Index("ix_investigation_audit_case_created", "case_id", "created_at"),
        Index("ix_investigation_audit_scan_created", "scan_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("investigation_cases.id", ondelete="RESTRICT"), nullable=True
    )
    scan_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("analysis_scans.id", ondelete="RESTRICT"), nullable=True
    )
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    event_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScanChunkModel(Base):
    __tablename__ = "scan_chunks"
    __table_args__ = (
        UniqueConstraint("scan_id", "chunk_index", name="uq_scan_chunk_index"),
        Index("ix_scan_chunks_scan_status", "scan_id", "status"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("analysis_scans.id", ondelete="RESTRICT"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    worker_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    employee_days_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    findings_persisted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checkpoint_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class AIInvestigatorSummaryModel(Base):
    __tablename__ = "ai_investigator_summaries"
    __table_args__ = (
        Index("ix_ai_summary_case_created", "case_id", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("investigation_cases.id", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(80), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

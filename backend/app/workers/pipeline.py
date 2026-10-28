from dataclasses import dataclass
from datetime import date
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import (
    AnalysisScanModel,
    IngestionProgressModel,
    IngestionRunModel,
    SessionSnapshotModel,
)
from app.application.normalized import NormalizedLoginSession
from app.application.snapshot_hash import canonical_hash
from app.investigations.models import ComparisonEligibilityMode
from app.investigations.service import persist_finding
from app.rules.historical_comparison import (
    ManagerDecisionObservation,
    evaluate_manager_decision_reversals_detailed,
)
from app.rules.engine import IntegrityRuleEngine
from app.timeline.analysis import analyze_employee_day
from app.timeline.builder import load_employee_day_timeline

ENGINE_VERSION = "0.9.0"
RULE_VERSION = "builtin-24-v1"


@dataclass(frozen=True, slots=True)
class QF001ReadOnlyEvaluation:
    findings: tuple
    selected_mode: str
    run_statuses: dict[str, str]
    reconciliation_statuses: dict[str, str]
    reconciliation_details: dict[str, dict[str, object]]
    limitations: tuple[str, ...]
    excluded_record_counts: dict[str, int]
    source_record_counts: dict[str, int]
    eligible: bool

async def process_employee_day(db: AsyncSession, *, scan_id: UUID, ingestion_run_id: UUID, agent_id: str, shift_date: date) -> int:
    timeline = await load_employee_day_timeline(db, ingestion_run_id=ingestion_run_id, agent_id=agent_id, shift_date=shift_date)
    if timeline is None:
        return 0
    assessment = IntegrityRuleEngine().evaluate(analyze_employee_day(timeline))
    inserted = 0
    for ordinal, f in enumerate(assessment.findings):
        key = f"{agent_id}:{shift_date.isoformat()}:{f.rule_id}:{f.source_session_id or '-'}:{ordinal}"
        evidence = {"rule_name": f.rule_name, "category": f.category.value, "metadata": f.metadata,
                    "evidence": [e.model_dump(mode="json") for e in f.evidence]}
        result = await persist_finding(
            db, scan_id=scan_id, finding_key=key, rule_id=f.rule_id,
            severity=f.severity.value, confidence=f.confidence,
            risk_contribution=f.risk_contribution, reason=f.reason,
            evidence_json=evidence, agent_id=agent_id, shift_date=shift_date,
            source_session_id=f.source_session_id,
        )
        inserted += int(result is not None)
    return inserted


def observation_from_session_snapshot(row: SessionSnapshotModel) -> ManagerDecisionObservation:
    """Map one stored snapshot and verify its hash with ingestion's canonical routine."""
    normalized = NormalizedLoginSession(
        source_system=row.source_system,
        source_session_id=row.source_session_id,
        agent_id=row.agent_id,
        supervisor_id=row.supervisor_id,
        manager_id=row.manager_id,
        site_id=row.site_id,
        site_name=row.site_name,
        team_id=row.team_id,
        shift_date=row.shift_date,
        start_at=row.start_at,
        end_at=row.end_at,
        status_id=row.status_id,
        dispute_reason_id=row.dispute_reason_id,
        dispute_state=row.dispute_state,
        supervisor_status_id=row.supervisor_status_id,
        ready_for_payroll=row.ready_for_payroll,
        payroll_adjusted=row.payroll_adjusted,
        payroll_adjusted_at=row.payroll_adjusted_at,
        session_added_by=row.session_added_by,
        add_session_reason_id=row.add_session_reason_id,
        agent_action_at=row.agent_action_at,
        supervisor_action_at=row.supervisor_action_at,
        manager_action_at=row.manager_action_at,
        multiple_logins=row.multiple_logins,
        agent_ip=row.agent_ip,
        machine_hostname=row.machine_hostname,
        primary_campaign_id=row.primary_campaign_id,
        primary_campaign_name=row.primary_campaign_name,
        metadata=row.metadata_json,
    )
    return ManagerDecisionObservation(
        snapshot_id=row.id,
        ingestion_run_id=row.ingestion_run_id,
        source_system=row.source_system,
        source_session_id=row.source_session_id,
        status_id=row.status_id,
        ready_for_payroll=row.ready_for_payroll,
        observed_at=row.observed_at,
        manager_action_at=row.manager_action_at,
        agent_id=row.agent_id,
        shift_date=row.shift_date,
        content_hash=row.content_hash,
        content_hash_verified=row.content_hash == canonical_hash(normalized),
    )


async def evaluate_qf001_observations(
    db: AsyncSession,
    *,
    earlier_run_id: UUID,
    later_run_id: UUID,
    date_from: date,
    date_to: date,
    eligibility_mode: ComparisonEligibilityMode = ComparisonEligibilityMode.STRICT_RECONCILED,
    override_role: str | None = None,
    override_reason: str | None = None,
):
    """Read-only, eligibility-aware evaluation for an explicitly selected run pair."""
    if earlier_run_id == later_run_id:
        raise ValueError("comparison ingestion runs must be distinct")
    if eligibility_mode == ComparisonEligibilityMode.OBSERVED_RECORDS_ONLY:
        if override_role not in {"manager", "admin"}:
            raise PermissionError("OBSERVED_RECORDS_ONLY requires manager or admin authorization")
        if override_reason is None or len(override_reason.strip()) < 10:
            raise ValueError("OBSERVED_RECORDS_ONLY requires a documented reason of at least 10 characters")
    earlier_run = await db.get(IngestionRunModel, earlier_run_id)
    later_run = await db.get(IngestionRunModel, later_run_id)
    if earlier_run is None or later_run is None:
        raise ValueError("both comparison ingestion runs must exist")
    if earlier_run.started_at is None or later_run.started_at is None:
        raise ValueError("comparison ingestion runs lack chronological timestamps")
    if later_run.started_at <= earlier_run.started_at:
        raise ValueError("later ingestion run is not chronologically after baseline")

    run_statuses: dict[str, str] = {}
    reconciliation_statuses: dict[str, str] = {}
    reconciliation_details: dict[str, dict[str, object]] = {}
    limitations: list[str] = []
    for run_id, run in ((earlier_run_id, earlier_run), (later_run_id, later_run)):
        progress = await db.get(IngestionProgressModel, run_id)
        run_statuses[str(run_id)] = run.status
        reconciliation_statuses[str(run_id)] = (
            f"{progress.completion_status}/{progress.reconciliation_status}"
            if progress is not None
            else "CHECKPOINTS_UNAVAILABLE"
        )
        reconciliation_details[str(run_id)] = (
            {
                "expected_sessions": progress.expected_session_count,
                "sessions_retrieved": progress.sessions_retrieved_count,
                "sessions_persisted": progress.sessions_persisted_count,
                "sessions_with_completed_activities": progress.sessions_with_completed_activities,
                "source_count_mismatches": list(progress.source_count_mismatches_json or []),
                "date_coverage": progress.date_coverage_json or {},
            }
            if progress is not None
            else {}
        )
        if run.status not in {"complete", "completed"}:
            limitations.append(f"run {run_id} status is {run.status}")
        if progress is None:
            limitations.append(f"run {run_id} has no reconciliation checkpoint")
        else:
            if progress.completion_status != "COMPLETE":
                limitations.append(
                    f"run {run_id} completion is {progress.completion_status}"
                )
            if progress.reconciliation_status != "RECONCILED":
                limitations.append(
                    f"run {run_id} reconciliation is {progress.reconciliation_status}"
                )
            if progress.expected_session_count is None:
                limitations.append(f"run {run_id} has no authoritative expected session count")

    async def observations(run_id: UUID) -> list[ManagerDecisionObservation]:
        result = await db.execute(
            select(SessionSnapshotModel).where(
                SessionSnapshotModel.ingestion_run_id == run_id,
                SessionSnapshotModel.shift_date >= date_from,
                SessionSnapshotModel.shift_date <= date_to,
            )
        )
        return [observation_from_session_snapshot(row) for row in result.scalars().all()]

    earlier = await observations(earlier_run_id)
    later = await observations(later_run_id)
    comparison = evaluate_manager_decision_reversals_detailed(
        earlier,
        later,
        earlier_run_id=earlier_run_id,
        later_run_id=later_run_id,
    )
    eligible = not limitations
    findings = comparison.findings
    if eligibility_mode == ComparisonEligibilityMode.STRICT_RECONCILED and not eligible:
        findings = ()
    return QF001ReadOnlyEvaluation(
        findings=findings,
        selected_mode=eligibility_mode.value,
        run_statuses=run_statuses,
        reconciliation_statuses=reconciliation_statuses,
        reconciliation_details=reconciliation_details,
        limitations=tuple(limitations),
        excluded_record_counts=comparison.excluded_record_counts,
        source_record_counts={"earlier": len(earlier), "later": len(later)},
        eligible=eligible,
    )


async def process_qf001_scan(db: AsyncSession, scan: AnalysisScanModel) -> tuple[int, int, dict[str, object]]:
    """Persist a complete QF-001 comparison in the caller's scan transaction."""
    if scan.baseline_ingestion_run_id is None:
        raise ValueError("historical_comparison scan requires a baseline ingestion run")
    mode = ComparisonEligibilityMode(scan.eligibility_mode)
    evaluation = await evaluate_qf001_observations(
        db,
        earlier_run_id=scan.baseline_ingestion_run_id,
        later_run_id=scan.ingestion_run_id,
        date_from=scan.date_from,
        date_to=scan.date_to,
        eligibility_mode=mode,
        override_role=scan.eligibility_override_role,
        override_reason=scan.eligibility_override_reason,
    )
    if mode == ComparisonEligibilityMode.STRICT_RECONCILED and not evaluation.eligible:
        raise RuntimeError("STRICT_RECONCILED requires both ingestions complete and reconciled")
    context: dict[str, object] = {
        "eligibility_mode": evaluation.selected_mode,
        "run_statuses": evaluation.run_statuses,
        "reconciliation_statuses": evaluation.reconciliation_statuses,
        "reconciliation_details": evaluation.reconciliation_details,
        "reconciliation_limitations": list(evaluation.limitations),
        "excluded_record_counts": evaluation.excluded_record_counts,
        "source_record_counts": evaluation.source_record_counts,
        "override_actor": scan.requested_by if mode == ComparisonEligibilityMode.OBSERVED_RECORDS_ONLY else None,
        "override_role": scan.eligibility_override_role,
        "override_reason": scan.eligibility_override_reason,
    }
    inserted = 0
    for finding in evaluation.findings:
        later = finding.metadata["later"]
        evidence = {
            "rule_name": finding.rule_name,
            "category": finding.category.value,
            "metadata": finding.metadata,
            "comparison_context": context,
            "evidence": [],
        }
        persisted = await persist_finding(
            db,
            scan_id=scan.id,
            finding_key=str(finding.metadata["finding_key"]),
            rule_id=finding.rule_id,
            severity=finding.severity.value,
            confidence=finding.confidence,
            risk_contribution=finding.risk_contribution,
            reason=finding.reason,
            evidence_json=evidence,
            agent_id=str(later["agent_id"]),
            shift_date=date.fromisoformat(str(later["shift_date"])),
            source_session_id=finding.source_session_id,
            stable_immutable_hash=True,
        )
        inserted += int(persisted is not None)
    return len(evaluation.findings), inserted, context

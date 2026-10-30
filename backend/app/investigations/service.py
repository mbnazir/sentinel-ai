from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert as pg_insert

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    AnalysisScanModel,
    CaseFindingModel,
    DurableFindingModel,
    IngestionRunModel,
    InvestigationAuditEventModel,
    InvestigationCaseModel,
)
from app.investigations.hashing import immutable_finding_hash
from app.investigations.models import (
    CaseCreate,
    CaseDisposition,
    CaseStatus,
    CaseUpdate,
    ScanCreate,
    ScanStatus,
)
from app.investigations.workflow import can_transition


class ImmutableFindingConflictError(RuntimeError):
    """A deterministic finding identity was replayed with changed evidence."""


async def create_scan(
    db: AsyncSession, payload: ScanCreate, *, actor_role: str | None = None
) -> AnalysisScanModel:
    if payload.date_to < payload.date_from:
        raise ValueError("date_to must be on or after date_from")
    if payload.scope == "historical_comparison":
        if payload.baseline_ingestion_run_id is None:
            raise ValueError("historical_comparison requires baseline_ingestion_run_id")
        if payload.baseline_ingestion_run_id == payload.ingestion_run_id:
            raise ValueError("comparison ingestion runs must be distinct")
        earlier = await db.get(IngestionRunModel, payload.baseline_ingestion_run_id)
        later = await db.get(IngestionRunModel, payload.ingestion_run_id)
        if earlier is None or later is None:
            raise ValueError("both comparison ingestion runs must exist")
        earlier_started = earlier.started_at
        later_started = later.started_at
        if earlier_started is None or later_started is None or later_started <= earlier_started:
            raise ValueError("ingestion_run_id must be chronologically later than baseline_ingestion_run_id")
    elif payload.baseline_ingestion_run_id is not None:
        raise ValueError("baseline_ingestion_run_id is only valid for historical_comparison scans")
    if payload.eligibility_mode.value == "OBSERVED_RECORDS_ONLY":
        if payload.scope != "historical_comparison":
            raise ValueError("observed-records eligibility is only valid for historical_comparison")
        if actor_role not in {"manager", "admin"}:
            raise PermissionError("OBSERVED_RECORDS_ONLY requires manager or admin authorization")
        if payload.eligibility_override_reason is None or len(payload.eligibility_override_reason.strip()) < 10:
            raise ValueError("OBSERVED_RECORDS_ONLY requires a documented reason of at least 10 characters")
    elif payload.eligibility_override_reason is not None:
        raise ValueError("eligibility_override_reason requires OBSERVED_RECORDS_ONLY mode")
    scan = AnalysisScanModel(
        id=uuid4(),
        ingestion_run_id=payload.ingestion_run_id,
        baseline_ingestion_run_id=payload.baseline_ingestion_run_id,
        eligibility_mode=payload.eligibility_mode.value,
        eligibility_override_reason=payload.eligibility_override_reason.strip()
        if payload.eligibility_override_reason
        else None,
        eligibility_override_role=actor_role if payload.eligibility_mode.value == "OBSERVED_RECORDS_ONLY" else None,
        date_from=payload.date_from,
        date_to=payload.date_to,
        requested_by=payload.requested_by,
        scope=payload.scope,
        status=ScanStatus.PENDING.value,
    )
    db.add(scan)
    db.add(InvestigationAuditEventModel(
        id=uuid4(), scan_id=scan.id, actor=payload.requested_by,
        event_type="scan_created",
        event_json={
            "date_from": str(payload.date_from),
            "date_to": str(payload.date_to),
            "scope": payload.scope,
            "ingestion_run_id": str(payload.ingestion_run_id),
            "baseline_ingestion_run_id": str(payload.baseline_ingestion_run_id)
            if payload.baseline_ingestion_run_id
            else None,
            "eligibility_mode": payload.eligibility_mode.value,
            "eligibility_override_reason": payload.eligibility_override_reason,
            "eligibility_override_role": actor_role
            if payload.eligibility_mode.value == "OBSERVED_RECORDS_ONLY"
            else None,
        },
    ))
    await db.commit()
    await db.refresh(scan)
    return scan


async def persist_finding(
    db: AsyncSession,
    *,
    scan_id: UUID,
    finding_key: str,
    rule_id: str,
    severity: str,
    confidence: float,
    risk_contribution: float,
    reason: str,
    evidence_json: dict[str, object],
    agent_id: str | None = None,
    shift_date=None,
    source_session_id: str | None = None,
    stable_immutable_hash: bool = False,
) -> DurableFindingModel | None:
    # The caller owns the transaction. No commits here.
    payload = {
        "scan_id": str(scan_id), "finding_key": finding_key, "rule_id": rule_id,
        "severity": severity, "confidence": confidence, "risk_contribution": risk_contribution,
        "reason": reason, "evidence_json": evidence_json, "agent_id": agent_id,
        "shift_date": str(shift_date) if shift_date else None,
        "source_session_id": source_session_id,
    }
    values = dict(
        id=uuid4(), scan_id=scan_id, finding_key=finding_key, agent_id=agent_id,
        shift_date=shift_date, source_session_id=source_session_id, rule_id=rule_id,
        severity=severity, confidence=confidence, risk_contribution=risk_contribution,
        reason=reason, evidence_json=evidence_json,
        immutable_hash=immutable_finding_hash(payload),
    )
    immutable_payload = payload
    if stable_immutable_hash:
        immutable_payload = {
            "finding_key": finding_key,
            "rule_id": rule_id,
            "severity": severity,
            "confidence": confidence,
            "risk_contribution": risk_contribution,
            "reason": reason,
            "evidence_json": evidence_json,
            "agent_id": agent_id,
            "shift_date": str(shift_date) if shift_date else None,
            "source_session_id": source_session_id,
        }
        values["immutable_hash"] = immutable_finding_hash(immutable_payload)
    stmt = pg_insert(DurableFindingModel).values(**values)
    if rule_id == "QF-001" and stable_immutable_hash:
        stmt = stmt.on_conflict_do_nothing(
            index_elements=[DurableFindingModel.finding_key],
            index_where=text("rule_id = 'QF-001'"),
        )
    else:
        stmt = stmt.on_conflict_do_nothing(constraint="uq_durable_finding_scan_key")
    stmt = stmt.returning(DurableFindingModel.id)
    inserted_id = (await db.execute(stmt)).scalar_one_or_none()
    if inserted_id is None:
        if rule_id == "QF-001" and stable_immutable_hash:
            existing = await db.scalar(
                select(DurableFindingModel).where(
                    DurableFindingModel.rule_id == rule_id,
                    DurableFindingModel.finding_key == finding_key,
                )
            )
            if existing is not None and existing.immutable_hash != values["immutable_hash"]:
                raise ImmutableFindingConflictError(
                    "QF-001 finding identity already exists with different immutable evidence"
                )
        return None
    return await db.get(DurableFindingModel, inserted_id)



async def create_case(db: AsyncSession, payload: CaseCreate) -> InvestigationCaseModel:
    case_id = uuid4()
    case = InvestigationCaseModel(
        id=case_id,
        case_number=f"SNT-{str(case_id).split('-')[0].upper()}",
        title=payload.title,
        status=CaseStatus.OPEN.value,
        disposition=CaseDisposition.UNDETERMINED.value,
        assigned_to=payload.assigned_to,
        created_by=payload.created_by,
    )
    db.add(case)
    if payload.finding_ids:
        result = await db.execute(select(DurableFindingModel.id).where(DurableFindingModel.id.in_(payload.finding_ids)))
        existing = set(result.scalars().all())
        missing = set(payload.finding_ids) - existing
        if missing:
            raise ValueError(f"Unknown finding ids: {sorted(str(x) for x in missing)}")
        for finding_id in payload.finding_ids:
            db.add(CaseFindingModel(id=uuid4(), case_id=case.id, finding_id=finding_id))
    db.add(InvestigationAuditEventModel(
        id=uuid4(), case_id=case.id, actor=payload.created_by, event_type="case_created",
        event_json={"title": payload.title, "finding_ids": [str(x) for x in payload.finding_ids]},
    ))
    await db.commit()
    await db.refresh(case)
    return case


async def update_case(db: AsyncSession, case_id: UUID, payload: CaseUpdate) -> InvestigationCaseModel:
    # Serialize updates and refresh even if this session already loaded the case.
    case = await db.get(
        InvestigationCaseModel, case_id, with_for_update=True, populate_existing=True,
    )
    if case is None:
        raise LookupError("case not found")
    before = {"status": case.status, "disposition": case.disposition, "assigned_to": case.assigned_to}
    if payload.status is not None:
        current = CaseStatus(case.status)
        if not can_transition(current, payload.status):
            raise ValueError(f"invalid case transition {current.value} -> {payload.status.value}")
        case.status = payload.status.value
    if payload.disposition is not None:
        if payload.disposition != CaseDisposition.UNDETERMINED and payload.status not in {CaseStatus.RESOLVED, CaseStatus.CLOSED} and case.status not in {CaseStatus.RESOLVED.value, CaseStatus.CLOSED.value}:
            raise ValueError("a final disposition requires resolved or closed status")
        case.disposition = payload.disposition.value
    if payload.assigned_to is not None:
        case.assigned_to = payload.assigned_to
    after = {"status": case.status, "disposition": case.disposition,
             "assigned_to": case.assigned_to}
    if before == after and not (payload.note or "").strip():
        # A repeated click without a change or note is not a new audit event.
        return case
    case.updated_at = datetime.now(timezone.utc)
    db.add(InvestigationAuditEventModel(
        id=uuid4(), case_id=case.id, actor=payload.actor, event_type="case_updated",
        event_json={
            "before": before,
            "after": after,
            "note": payload.note,
        },
    ))
    await db.commit()
    await db.refresh(case)
    return case

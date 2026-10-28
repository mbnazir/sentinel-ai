from __future__ import annotations
from sqlalchemy.dialects.postgresql import insert as pg_insert

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import (
    AnalysisScanModel,
    CaseFindingModel,
    DurableFindingModel,
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


async def create_scan(db: AsyncSession, payload: ScanCreate) -> AnalysisScanModel:
    if payload.date_to < payload.date_from:
        raise ValueError("date_to must be on or after date_from")
    scan = AnalysisScanModel(
        id=uuid4(),
        ingestion_run_id=payload.ingestion_run_id,
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
        event_json={"date_from": str(payload.date_from), "date_to": str(payload.date_to), "scope": payload.scope},
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
    stmt = pg_insert(DurableFindingModel).values(**values).on_conflict_do_nothing(
        constraint="uq_durable_finding_scan_key"
    ).returning(DurableFindingModel.id)
    inserted_id = (await db.execute(stmt)).scalar_one_or_none()
    if inserted_id is None:
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
    case = await db.get(InvestigationCaseModel, case_id)
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
    case.updated_at = datetime.now(timezone.utc)
    db.add(InvestigationAuditEventModel(
        id=uuid4(), case_id=case.id, actor=payload.actor, event_type="case_updated",
        event_json={
            "before": before,
            "after": {"status": case.status, "disposition": case.disposition, "assigned_to": case.assigned_to},
            "note": payload.note,
        },
    ))
    await db.commit()
    await db.refresh(case)
    return case

from collections import Counter
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.infrastructure.models import (
    AnalysisScanModel,
    DurableFindingModel,
    InvestigationCaseModel,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(
    scan_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if scan_id is None:
        latest = await db.execute(
            select(AnalysisScanModel).order_by(AnalysisScanModel.started_at.desc()).limit(1)
        )
        scan = latest.scalar_one_or_none()
    else:
        scan = await db.get(AnalysisScanModel, scan_id)

    findings: list[DurableFindingModel] = []
    if scan is not None:
        result = await db.execute(
            select(DurableFindingModel).where(DurableFindingModel.scan_id == scan.id)
        )
        findings = list(result.scalars())

    open_cases = (
        await db.execute(
            select(func.count())
            .select_from(InvestigationCaseModel)
            .where(InvestigationCaseModel.status.not_in(["resolved", "closed"]))
        )
    ).scalar_one()

    severity = Counter(item.severity for item in findings)
    rules = Counter(item.rule_id for item in findings)
    agent_risk: Counter[str] = Counter()
    for item in findings:
        if item.agent_id:
            agent_risk[item.agent_id] += int(round(item.risk_contribution))

    return {
        "scan": None if scan is None else {
            "id": str(scan.id),
            "status": scan.status,
            "date_from": str(scan.date_from),
            "date_to": str(scan.date_to),
            "employee_days_processed": scan.employee_days_processed,
            "finding_count": scan.finding_count,
            "total_chunks": scan.total_chunks,
            "completed_chunks": scan.completed_chunks,
            "failed_chunks": scan.failed_chunks,
            "engine_version": scan.engine_version,
            "rule_version": scan.rule_version,
        },
        "kpis": {
            "total_findings": len(findings),
            "critical_findings": severity.get("critical", 0),
            "high_findings": severity.get("high", 0),
            "open_cases": open_cases,
        },
        "severity_distribution": dict(severity),
        "top_rules": [{"rule_id": k, "count": v} for k, v in rules.most_common(10)],
        "top_agents": [
            {"agent_id": k, "risk_points": v} for k, v in agent_risk.most_common(10)
        ],
    }


@router.get("/findings")
async def findings(
    scan_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    result = await db.execute(
        select(DurableFindingModel)
        .where(DurableFindingModel.scan_id == scan_id)
        .order_by(DurableFindingModel.risk_contribution.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(item.id),
            "agent_id": item.agent_id,
            "shift_date": str(item.shift_date) if item.shift_date else None,
            "session_id": item.source_session_id,
            "rule_id": item.rule_id,
            "severity": item.severity,
            "confidence": item.confidence,
            "risk_contribution": item.risk_contribution,
            "reason": item.reason,
        }
        for item in result.scalars()
    ]


@router.get("/cases")
async def cases(
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    result = await db.execute(
        select(InvestigationCaseModel)
        .order_by(InvestigationCaseModel.updated_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(item.id),
            "case_number": item.case_number,
            "title": item.title,
            "status": item.status,
            "disposition": item.disposition,
            "assigned_to": item.assigned_to,
            "created_by": item.created_by,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in result.scalars()
    ]


@router.get("/scans")
async def scans(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    result = await db.execute(
        select(AnalysisScanModel).order_by(AnalysisScanModel.started_at.desc()).limit(limit)
    )
    return [
        {
            "id": str(item.id),
            "status": item.status,
            "date_from": str(item.date_from),
            "date_to": str(item.date_to),
            "employee_days_processed": item.employee_days_processed,
            "finding_count": item.finding_count,
            "total_chunks": item.total_chunks,
            "completed_chunks": item.completed_chunks,
            "failed_chunks": item.failed_chunks,
            "finalization_status": item.finalization_status,
        }
        for item in result.scalars()
    ]


@router.get("/findings/{finding_id}")
async def finding_detail(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    item = await db.get(DurableFindingModel, finding_id)
    if item is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="finding not found")
    return {
        "id": str(item.id),
        "scan_id": str(item.scan_id),
        "agent_id": item.agent_id,
        "shift_date": str(item.shift_date) if item.shift_date else None,
        "session_id": item.source_session_id,
        "rule_id": item.rule_id,
        "severity": item.severity,
        "confidence": item.confidence,
        "risk_contribution": item.risk_contribution,
        "reason": item.reason,
        "evidence": item.evidence_json,
        "immutable_hash": item.immutable_hash,
    }

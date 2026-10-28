from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.weekly.builder import load_payroll_week
from app.weekly.models import PayrollWeek, WeeklySession
from app.weekly.activity_repository import load_activity_comparison
from collections import Counter

router = APIRouter(prefix="/weekly", tags=["weekly payroll"])


@router.get("/{employee_id}/{day}")
async def get_weekly_payroll_context(employee_id: str, day: date, ingestion_run_id: UUID,
                                    db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    week, sessions = await load_payroll_week(db, ingestion_run_id=ingestion_run_id,
                                             employee_id=employee_id, day=day)
    if not sessions:
        raise HTTPException(status_code=404, detail="Employee payroll week not found in ingestion run")
    quality = week.completeness.value
    verified = (quality == "COMPLETE" and week.source_count_reconciled
                and week.provenance.get("ingestion_run_status") == "completed")
    response_quality = quality if verified or quality == "INCOMPLETE" else "UNVERIFIED"
    return {"payroll_week": week.model_dump(mode="json"),
            "sessions": [s.model_dump(mode="json") for s in sessions],
            "completeness_status": response_quality,
            "analysis_status": "VERIFIED" if verified else "PROVISIONAL",
            "verified_financial_impact_available": False,
            "readiness_reasons": ["Source record counts are not reconciled",
                                  "Quartz payable-hour units and baseline authority are unconfirmed",
                                  "No verified payable baseline reconstruction is available"]}


@router.get("/{employee_id}/{day}/activity-changes")
async def get_activity_changes(
    employee_id: str,
    day: date,
    ingestion_run_id: UUID,
    source_session_id: str,
    original_source_id: int = Query(default=2, ge=0, le=5),
    revised_source_id: int = Query(default=3, ge=0, le=5),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if original_source_id == revised_source_id:
        raise HTTPException(status_code=422, detail="Compared source versions must be different")
    comparison = await load_activity_comparison(db, ingestion_run_id=ingestion_run_id,
        employee_id=employee_id, day=day, source_session_id=source_session_id,
        original_source_id=original_source_id, revised_source_id=revised_source_id)
    if comparison is None:
        # Avoid disclosing whether a session exists for another employee or run.
        raise HTTPException(status_code=404, detail="Session not found for employee and ingestion run")
    return {
        "employee_id": employee_id,
        "session_id": comparison.source_session_id,
        "ingestion_run_id": str(comparison.ingestion_run_id),
        "compared_versions": {
            "original": comparison.original_version.version_id if comparison.original_version else None,
            "revised": comparison.revised_version.version_id if comparison.revised_version else None,
        },
        "change_summary": {
            "change_count": len(comparison.changes),
            "change_types": dict(Counter(change.change_type.value for change in comparison.changes)),
            "reclassified_seconds": str(comparison.reclassified_seconds),
            "net_covered_seconds": (str(comparison.net_covered_seconds)
                                     if comparison.net_covered_seconds is not None else None),
        },
        "interval_changes": [change.model_dump(mode="json") for change in comparison.changes],
        "readiness": comparison.readiness.model_dump(mode="json"),
        "finding": comparison.finding,
        "editor_identity": "UNVERIFIED",
        "financial_impact": "UNVERIFIED",
        "missing_evidence": list(comparison.readiness.reasons) + [
            "Quartz activity snapshots do not provide independently verified editor identity",
            "Payable eligibility, payroll rates, and monetary impact are not established",
        ],
    }

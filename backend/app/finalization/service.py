from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.models import AnalysisScanModel, DurableFindingModel, ScanChunkModel
from app.finalization.models import ScanSummary

async def summarize_scan(db:AsyncSession, scan:AnalysisScanModel)->ScanSummary:
    result=await db.execute(select(DurableFindingModel).where(DurableFindingModel.scan_id==scan.id))
    findings=list(result.scalars())
    behavioral=sum(f.rule_id.startswith("BA-") for f in findings)
    organizational=sum(f.rule_id.startswith("OI-") for f in findings)
    deterministic=len(findings)-behavioral-organizational
    high=sum(f.severity in {"high","critical"} for f in findings)
    return ScanSummary(
        employee_days=scan.employee_days_processed,
        deterministic_findings=deterministic,
        behavioral_findings=behavioral,
        organizational_findings=organizational,
        total_findings=len(findings),
        high_or_critical=high,
        max_risk_score=min(100.0,max((f.risk_contribution for f in findings),default=0.0)),
    )

async def scan_is_ready_for_finalization(db:AsyncSession, scan_id)->bool:
    rows=(await db.execute(select(ScanChunkModel.status).where(ScanChunkModel.scan_id==scan_id))).scalars().all()
    return bool(rows) and all(x=="completed" for x in rows)

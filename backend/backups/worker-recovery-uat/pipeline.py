from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.investigations.service import persist_finding
from app.rules.engine import IntegrityRuleEngine
from app.timeline.analysis import analyze_employee_day
from app.timeline.builder import load_employee_day_timeline

ENGINE_VERSION = "0.9.0"
RULE_VERSION = "builtin-24-v1"

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

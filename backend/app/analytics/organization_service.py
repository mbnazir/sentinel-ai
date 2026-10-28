from collections import defaultdict
from datetime import date
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.organization_engine import assess_organization
from app.analytics.organization_models import OrganizationalAssessment, OrganizationalDailyBehavior
from app.domain.data_sources import ActivityDataSource
from app.infrastructure.models import SessionSnapshotModel
from app.rules.context import IntegrityPolicy, RuleContext
from app.rules.engine import IntegrityRuleEngine
from app.timeline.analysis import analyze_employee_day
from app.timeline.builder import load_employee_day_timeline

MAX_EMPLOYEE_DAYS=500

async def build_organizational_assessment(db:AsyncSession,*,ingestion_run_id:UUID,date_from:date,date_to:date)->OrganizationalAssessment:
    if date_to<date_from: raise ValueError('date_to must not be before date_from')
    if (date_to-date_from).days>90: raise ValueError('organizational analysis window cannot exceed 91 shift dates')
    result=await db.execute(select(SessionSnapshotModel).where(SessionSnapshotModel.ingestion_run_id==ingestion_run_id,SessionSnapshotModel.shift_date>=date_from,SessionSnapshotModel.shift_date<=date_to).order_by(SessionSnapshotModel.agent_id,SessionSnapshotModel.shift_date))
    sessions=list(result.scalars())
    keys=sorted({(r.agent_id,r.shift_date) for r in sessions})
    if len(keys)>MAX_EMPLOYEE_DAYS: raise ValueError(f'analysis contains {len(keys)} employee-days; maximum synchronous limit is {MAX_EMPLOYEE_DAYS}')
    meta=defaultdict(list)
    for r in sessions: meta[(r.agent_id,r.shift_date)].append(r)
    engine=IntegrityRuleEngine(); policy=IntegrityPolicy(); rows=[]
    for agent,shift in keys:
        timeline=await load_employee_day_timeline(db,ingestion_run_id=ingestion_run_id,agent_id=agent,shift_date=shift)
        if timeline is None: continue
        analysis=analyze_employee_day(timeline); assessment=engine.evaluate(analysis); ctx=RuleContext(analysis=analysis,policy=policy)
        gain=0
        for session in timeline.sessions:
            captured=ctx.captured_seconds(session); _,manual=ctx.latest_manual_seconds(session); gain+=max(0,manual-captured)
        day_sessions=meta[(agent,shift)]; representative=day_sessions[0]
        rows.append(OrganizationalDailyBehavior(agent_id=agent,shift_date=shift,supervisor_id=representative.supervisor_id,manager_id=representative.manager_id,campaign_id=representative.primary_campaign_id,client_id=str(representative.primary_client_id) if representative.primary_client_id is not None else None,site_id=representative.site_id,team_id=representative.team_id,risk_score=assessment.risk_score,finding_count=assessment.finding_count,manual_gain_seconds=gain,rounded_additions=sum(f.rule_id=='SA-R010' for f in assessment.findings),payroll_edits=sum(f.rule_id=='SA-R004' for f in assessment.findings),supervisor_additions=sum(f.rule_id=='SA-R002' for f in assessment.findings),manager_additions=sum(f.rule_id=='SA-R003' for f in assessment.findings),payroll_adjustments=sum(bool(s.payroll_adjusted) for s in day_sessions),manager_interventions=sum(s.manager_action_at is not None for s in day_sessions)))
    return assess_organization(rows,date_from,date_to)

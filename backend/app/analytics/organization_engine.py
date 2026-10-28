from collections import Counter, defaultdict
from datetime import date
from statistics import mean, pstdev
from app.analytics.organization_models import (GroupRiskProfile, OrganizationalAssessment, OrganizationalDailyBehavior, OrganizationalLevel, RelationshipFinding)

def _level(score:float)->OrganizationalLevel:
    if score>=81:return OrganizationalLevel.CRITICAL
    if score>=61:return OrganizationalLevel.HIGH
    if score>=41:return OrganizationalLevel.ELEVATED
    if score>=21:return OrganizationalLevel.WATCH
    return OrganizationalLevel.NORMAL

def _profile(group_type:str, group_id:str, rows:list[OrganizationalDailyBehavior], date_from:date, date_to:date, findings:list[RelationshipFinding])->GroupRiskProfile:
    own=[r for r in rows if getattr(r, f"{group_type}_id", None)==group_id]
    allowed={
        'supervisor': ('supervisor_', 'payroll_supervisor_team', 'manager_supervisor_agent'),
        'manager': ('manager_', 'manager_supervisor_agent'),
        'campaign': ('campaign_',),
        'site': ('site_',),
    }[group_type]
    related=[f for f in findings if f.subject_ids and f.subject_ids[0]==group_id and any(f.relationship_type.startswith(prefix) for prefix in allowed)]
    score=min(100.0,sum(f.score for f in related))
    return GroupRiskProfile(group_type=group_type,group_id=group_id,date_from=date_from,date_to=date_to,employee_days=len(own),distinct_agents=len({r.agent_id for r in own}),manual_gain_seconds=sum(r.manual_gain_seconds for r in own),high_risk_days=sum(r.risk_score>=61 for r in own),payroll_adjustment_days=sum(r.payroll_adjustments>0 for r in own),score=score,level=_level(score),findings=tuple(related))

def _pair_findings(rows:list[OrganizationalDailyBehavior], actor_field:str, code:str, label:str)->list[RelationshipFinding]:
    events=defaultdict(list)
    for r in rows:
        actor=getattr(r, actor_field)
        additions=r.supervisor_additions if actor_field=='supervisor_id' else r.manager_additions
        if actor and additions>0: events[(actor,r.agent_id)].append(r)
    out=[]
    for (actor,agent),items in events.items():
        dates={x.shift_date for x in items}
        if len(dates)>=3:
            out.append(RelationshipFinding(code=code,relationship_type=f'{actor_field.removesuffix("_id")}_agent',subject_ids=(actor,agent),level=OrganizationalLevel.HIGH,score=min(45,20+5*len(dates)),reason=f'Repeated {label} time additions affect the same agent across multiple shift dates.',event_count=sum(x.supervisor_additions if actor_field=='supervisor_id' else x.manager_additions for x in items),distinct_shift_dates=len(dates),affected_agents=1))
    return out

def _concentration(rows:list[OrganizationalDailyBehavior], actor_field:str, code:str, label:str)->list[RelationshipFinding]:
    grouped=defaultdict(list)
    for r in rows:
        actor=getattr(r,actor_field)
        additions=r.supervisor_additions if actor_field=='supervisor_id' else r.manager_additions
        if actor and additions>0: grouped[actor].append(r)
    out=[]
    for actor,items in grouped.items():
        if len({r.shift_date for r in items})<4: continue
        counts=Counter(r.agent_id for r in items)
        total=sum(counts.values()); agent,n=counts.most_common(1)[0]
        if total>=4 and n/total>=.70:
            out.append(RelationshipFinding(code=code,relationship_type=f'{actor_field.removesuffix("_id")}_concentration',subject_ids=(actor,agent),level=OrganizationalLevel.HIGH,score=30,reason=f'{label} interventions are disproportionately concentrated on one agent.',event_count=total,distinct_shift_dates=len({r.shift_date for r in items}),affected_agents=len(counts),metadata={'concentration':round(n/total,3)}))
    return out


def _intervention_chain(rows:list[OrganizationalDailyBehavior])->list[RelationshipFinding]:
    grouped=defaultdict(list)
    for r in rows:
        if r.manager_id and r.supervisor_id and r.supervisor_additions>0 and r.manager_additions>0:
            grouped[(r.manager_id,r.supervisor_id,r.agent_id)].append(r)
    out=[]
    for (manager,supervisor,agent),items in grouped.items():
        dates={r.shift_date for r in items}
        if len(dates)>=3:
            out.append(RelationshipFinding(code='OI-R003',relationship_type='manager_supervisor_agent',subject_ids=(manager,supervisor,agent),level=OrganizationalLevel.HIGH,score=min(45,25+4*len(dates)),reason='The same manager and supervisor both increase time for the same agent across repeated shift dates. This is a relationship-risk signal requiring review of the underlying deterministic evidence.',event_count=len(items),distinct_shift_dates=len(dates),affected_agents=1))
    return out

def _payroll_team_concentration(rows:list[OrganizationalDailyBehavior])->list[RelationshipFinding]:
    adjusted=[r for r in rows if r.payroll_adjustments>0 and r.supervisor_id]
    if len(adjusted)<5:return []
    counts=Counter(r.supervisor_id for r in adjusted); sup,n=counts.most_common(1)[0]
    population_teams={r.supervisor_id for r in rows if r.supervisor_id}
    if len(population_teams)>=2 and n/len(adjusted)>=.60:
        return [RelationshipFinding(code='OI-P001',relationship_type='payroll_supervisor_team',subject_ids=(sup,),level=OrganizationalLevel.ELEVATED,score=22,reason='Payroll-adjusted employee-days are concentrated within one supervisor team. Payroll actor identity is unavailable, so this is a concentration signal rather than a collusion finding.',event_count=n,distinct_shift_dates=len({r.shift_date for r in adjusted if r.supervisor_id==sup}),affected_agents=len({r.agent_id for r in adjusted if r.supervisor_id==sup}),metadata={'share':round(n/len(adjusted),3)})]
    return []

def _group_outliers(rows:list[OrganizationalDailyBehavior], field:str, code:str, label:str)->list[RelationshipFinding]:
    totals=defaultdict(int); days=Counter()
    for r in rows:
        gid=getattr(r,field)
        if gid: totals[gid]+=r.manual_gain_seconds; days[gid]+=1
    if len(totals)<3:return []
    vals=list(totals.values()); mu=mean(vals); sd=pstdev(vals)
    if sd==0:return []
    out=[]
    for gid,val in totals.items():
        z=(val-mu)/sd
        if z>=2.0 and days[gid]>=5:
            out.append(RelationshipFinding(code=code,relationship_type=f'{field.removesuffix("_id")}_outlier',subject_ids=(gid,),level=OrganizationalLevel.ELEVATED,score=min(30,15+z*4),reason=f'{label} manual time gain is materially above peer groups.',event_count=days[gid],distinct_shift_dates=len({r.shift_date for r in rows if getattr(r,field)==gid}),affected_agents=len({r.agent_id for r in rows if getattr(r,field)==gid}),metadata={'z_score':round(z,2),'peer_mean_seconds':round(mu,2),'observed_seconds':val}))
    return out

def assess_organization(rows:list[OrganizationalDailyBehavior],date_from:date,date_to:date)->OrganizationalAssessment:
    findings=[]
    findings += _pair_findings(rows,'supervisor_id','OI-R001','Supervisor')
    findings += _concentration(rows,'supervisor_id','OI-S001','Supervisor')
    manager_available=any(r.manager_id for r in rows)
    if manager_available:
        findings += _pair_findings(rows,'manager_id','OI-R002','Manager')
        findings += _concentration(rows,'manager_id','OI-M001','Manager')
        findings += _intervention_chain(rows)
    findings += _payroll_team_concentration(rows)
    findings += _group_outliers(rows,'campaign_id','OI-C001','Campaign')
    findings += _group_outliers(rows,'site_id','OI-T001','Site')
    supervisors=sorted({r.supervisor_id for r in rows if r.supervisor_id})
    managers=sorted({r.manager_id for r in rows if r.manager_id})
    campaigns=sorted({r.campaign_id for r in rows if r.campaign_id})
    sites=sorted({r.site_id for r in rows if r.site_id})
    notes=[]
    if not manager_available: notes.append('Manager hierarchy is unavailable for this population; manager relationship analytics were not executed.')
    notes.append('Quartz activity data does not identify the Payroll actor; payroll concentration signals cannot attribute behavior to a specific payroll user.')
    return OrganizationalAssessment(date_from=date_from,date_to=date_to,employee_days_analyzed=len(rows),distinct_agents=len({r.agent_id for r in rows}),supervisor_profiles=tuple(_profile('supervisor',x,rows,date_from,date_to,findings) for x in supervisors),manager_profiles=tuple(_profile('manager',x,rows,date_from,date_to,findings) for x in managers),campaign_profiles=tuple(_profile('campaign',x,rows,date_from,date_to,findings) for x in campaigns),site_profiles=tuple(_profile('site',x,rows,date_from,date_to,findings) for x in sites),relationship_findings=tuple(sorted(findings,key=lambda f:(-f.score,f.code,f.subject_ids))),data_quality_notes=tuple(notes))

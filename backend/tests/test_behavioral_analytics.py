from datetime import date
from app.analytics.engine import build_agent_profile, pair_findings, supervisor_findings
from app.analytics.models import DailyBehavior

def row(agent,day,gain=0,risk=10,sup='S1',rounds=0,supadds=0):
 return DailyBehavior(agent_id=agent,shift_date=date(2026,8,day),supervisor_id=sup,campaign_id='C1',risk_score=risk,manual_gain_seconds=gain,rounded_additions=rounds,supervisor_additions=supadds)

def test_agent_peer_outlier_and_recurrence():
 own=[row('A1',d,7200,80,rounds=1) for d in range(1,6)]
 peers=own+[row(f'A{x}',1,300) for x in range(2,9)]
 p=build_agent_profile('A1',own,peers,date(2026,8,1),date(2026,8,5))
 codes={f.code for f in p.findings}
 assert 'BA-A001' in codes and 'BA-A002' in codes and 'BA-A003' in codes
 assert p.behavioral_score>0

def test_supervisor_concentration():
 rows=[row('A1',d,supadds=1) for d in range(1,5)]
 assert supervisor_findings('S1',rows)[0].code=='BA-S001'

def test_pair_pattern_requires_three_days():
 rows=[row('A1',d,supadds=1) for d in range(1,4)]
 assert pair_findings(rows)[0].code=='BA-C001'

def test_small_peer_group_does_not_claim_outlier():
 own=[row('A1',1,99999)]
 peers=own+[row('A2',1,1),row('A3',1,1)]
 p=build_agent_profile('A1',own,peers,date(2026,8,1),date(2026,8,1))
 assert 'BA-A001' not in {f.code for f in p.findings}

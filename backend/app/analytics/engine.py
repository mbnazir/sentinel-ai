from collections import Counter, defaultdict
from statistics import mean, pstdev
from app.analytics.models import BehavioralFinding, BehavioralLevel, BehavioralProfile, DailyBehavior

def _level(score:float)->BehavioralLevel:
    if score>=81:return BehavioralLevel.CRITICAL
    if score>=61:return BehavioralLevel.HIGH
    if score>=41:return BehavioralLevel.ELEVATED
    if score>=21:return BehavioralLevel.WATCH
    return BehavioralLevel.NORMAL

def _outlier(value:float, peers:list[float])->tuple[float,float]:
    if len(peers)<5:return 0.0, mean(peers) if peers else 0.0
    mu=mean(peers); sigma=pstdev(peers)
    if sigma==0:return (4.0 if value>mu else 0.0),mu
    return (value-mu)/sigma,mu

def build_agent_profile(subject_id:str, rows:list[DailyBehavior], peer_rows:list[DailyBehavior], date_from, date_to)->BehavioralProfile:
    own=[r for r in rows if r.agent_id==subject_id]
    gains=[r.manual_gain_seconds for r in own]; findings=[]
    peer_by_agent=defaultdict(int)
    for r in peer_rows: peer_by_agent[r.agent_id]+=r.manual_gain_seconds
    own_total=sum(gains); z,base=_outlier(own_total,list(peer_by_agent.values()))
    if z>=2.5:
        findings.append(BehavioralFinding(code='BA-A001',subject_type='agent',subject_id=subject_id,level=BehavioralLevel.HIGH if z<3.5 else BehavioralLevel.CRITICAL,score=min(35,15+z*5),reason='Manual time gain is materially above peer behavior.',observed=own_total,baseline=base,sample_size=len(peer_by_agent),metadata={'z_score':round(z,2)}))
    high=sum(r.risk_score>=61 for r in own)
    if len(own)>=5 and high/len(own)>=.4:
        findings.append(BehavioralFinding(code='BA-A002',subject_type='agent',subject_id=subject_id,level=BehavioralLevel.HIGH,score=25,reason='High-risk employee-days recur unusually often.',observed=high/len(own),baseline=.4,sample_size=len(own)))
    rounded=sum(r.rounded_additions for r in own)
    if rounded>=3:
        findings.append(BehavioralFinding(code='BA-A003',subject_type='agent',subject_id=subject_id,level=BehavioralLevel.ELEVATED,score=min(20,8+rounded*2),reason='Repeated round-number manual additions detected across shift dates.',observed=rounded,baseline=3,sample_size=len(own)))
    weekday=Counter(r.shift_date.weekday() for r in own if r.manual_gain_seconds>0)
    if sum(weekday.values())>=4 and weekday and max(weekday.values())/sum(weekday.values())>=.65:
        day,count=weekday.most_common(1)[0]; findings.append(BehavioralFinding(code='BA-A004',subject_type='agent',subject_id=subject_id,level=BehavioralLevel.WATCH,score=12,reason='Manual gains are concentrated on one day of the week.',observed=count/sum(weekday.values()),baseline=.65,sample_size=sum(weekday.values()),metadata={'weekday':day}))
    score=min(100,sum(f.score for f in findings))
    return BehavioralProfile(subject_type='agent',subject_id=subject_id,date_from=date_from,date_to=date_to,days_observed=len(own),total_manual_gain_seconds=own_total,average_daily_gain_seconds=round(mean(gains),2) if gains else 0,high_risk_days=high,behavioral_score=score,level=_level(score),findings=tuple(findings))

def supervisor_findings(supervisor_id:str, rows:list[DailyBehavior])->tuple[BehavioralFinding,...]:
    own=[r for r in rows if r.supervisor_id==supervisor_id]; out=[]
    affected={r.agent_id for r in own if r.supervisor_additions>0}
    additions=sum(r.supervisor_additions for r in own)
    if additions>=3 and len(affected)==1:
        out.append(BehavioralFinding(code='BA-S001',subject_type='supervisor',subject_id=supervisor_id,level=BehavioralLevel.HIGH,score=30,reason='Supervisor-added time is repeatedly concentrated on the same agent.',observed=additions,baseline=None,sample_size=len(own),metadata={'agent_id':next(iter(affected))}))
    return tuple(out)

def pair_findings(rows:list[DailyBehavior])->tuple[BehavioralFinding,...]:
    pairs=Counter((r.supervisor_id,r.agent_id) for r in rows if r.supervisor_id and r.supervisor_additions>0)
    return tuple(BehavioralFinding(code='BA-C001',subject_type='supervisor_agent_pair',subject_id=f'{s}:{a}',level=BehavioralLevel.HIGH,score=min(40,20+n*3),reason='Repeated supervisor time additions affect the same agent across multiple shift dates.',observed=n,baseline=3,sample_size=n,metadata={'supervisor_id':s,'agent_id':a}) for (s,a),n in pairs.items() if n>=3)

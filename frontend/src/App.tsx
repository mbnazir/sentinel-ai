import { useEffect, useMemo, useRef, useState } from "react";
import { NavLink, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { api, CaseRow, Finding, Overview, ScanRow } from "./api";
import { HistoricalDecisionEvidence } from "./HistoricalDecisionEvidence";

const severityClass = (s: string) => `badge ${s.toLowerCase()}`;

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="mark">S</div><div><strong>Sentinel AI</strong><span>Workforce Integrity</span></div></div>
      <nav>
        <NavLink to="/">Overview</NavLink>
        <NavLink to="/findings">Findings</NavLink>
        <NavLink to="/cases">Investigations</NavLink>
        <NavLink to="/scans">Scans</NavLink>
      </nav>
      <div className="sidebar-foot">Engine v0.11.0<br/>Evidence-led. Human-reviewed.</div>
    </aside>
    <main className="content">{children}</main>
  </div>;
}

function PageHead({title, sub}:{title:string;sub:string}) {
  return <div className="page-head"><div><h1>{title}</h1><p>{sub}</p></div></div>;
}

function Metric({label,value,detail}:{label:string;value:string|number;detail?:string}) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</div>;
}

function OverviewPage() {
  const [data,setData]=useState<Overview|null>(null);
  const [err,setErr]=useState("");
  useEffect(()=>{ api.overview().then(setData).catch(e=>setErr(String(e))); },[]);
  if(err) return <ErrorBox text={err}/>;
  if(!data) return <Loading/>;

  const scan=data.scan;
  const maxSeverity=Math.max(1,...Object.values(data.severity_distribution));
  return <>
    <PageHead title="Integrity Overview" sub="Prioritized workforce integrity signals from the latest completed analysis."/>
    <div className="metrics">
      <Metric label="Total Findings" value={data.kpis.total_findings}/>
      <Metric label="Critical" value={data.kpis.critical_findings}/>
      <Metric label="High Risk" value={data.kpis.high_findings}/>
      <Metric label="Open Cases" value={data.kpis.open_cases}/>
    </div>

    {scan && <div className="scan-strip">
      <div><span>Current scan</span><strong>{scan.date_from} → {scan.date_to}</strong></div>
      <div><span>Status</span><strong className="status-text">{scan.status}</strong></div>
      <div><span>Employee-days</span><strong>{scan.employee_days_processed}</strong></div>
      <div><span>Chunks</span><strong>{scan.completed_chunks}/{scan.total_chunks}</strong></div>
      <div><span>Engine</span><strong>{scan.engine_version || "—"}</strong></div>
    </div>}

    <div className="grid2">
      <section className="panel">
        <div className="panel-title"><h2>Severity Distribution</h2><span>Latest scan</span></div>
        <div className="bars">
          {["critical","high","medium","low","info"].map(k=>{
            const v=data.severity_distribution[k]||0;
            return <div className="barrow" key={k}><label>{k}</label><div className="track"><i style={{width:`${(v/maxSeverity)*100}%`}}/></div><b>{v}</b></div>
          })}
        </div>
      </section>
      <section className="panel">
        <div className="panel-title"><h2>Highest Risk Agents</h2><span>Accumulated risk points</span></div>
        <div className="rank-list">
          {data.top_agents.length ? data.top_agents.map((x,i)=><div key={x.agent_id}><span className="rank">{i+1}</span><strong>{x.agent_id}</strong><b>{x.risk_points}</b></div>) : <Empty text="No agent risk data in this scan."/>}
        </div>
      </section>
    </div>

    <section className="panel">
      <div className="panel-title"><h2>Most Triggered Rules</h2><span>Deterministic and population findings</span></div>
      <div className="rule-grid">
        {data.top_rules.map(r=><div key={r.rule_id}><code>{r.rule_id}</code><strong>{r.count}</strong></div>)}
      </div>
    </section>
  </>;
}

function FindingsPage() {
  const [scans,setScans]=useState<ScanRow[]>([]);
  const [scanId,setScanId]=useState("");
  const [rows,setRows]=useState<Finding[]>([]);
  const [filter,setFilter]=useState("");
  const navigate=useNavigate();
  useEffect(()=>{ api.scans().then(x=>{setScans(x); if(x[0]) setScanId(x[0].id)}); },[]);
  useEffect(()=>{ if(scanId) api.findings(scanId).then(setRows); },[scanId]);
  const visible=useMemo(()=>rows.filter(x=>!filter || [x.agent_id,x.rule_id,x.severity,x.reason].some(v=>(v||"").toLowerCase().includes(filter.toLowerCase()))),[rows,filter]);
  return <>
    <PageHead title="Findings" sub="Immutable, evidence-linked analytical findings. A finding is not a fraud determination."/>
    <div className="toolbar">
      <select value={scanId} onChange={e=>setScanId(e.target.value)}>{scans.map(s=><option value={s.id} key={s.id}>{s.date_from} → {s.date_to} · {s.status}</option>)}</select>
      <input placeholder="Filter agent, rule, severity, reason…" value={filter} onChange={e=>setFilter(e.target.value)}/>
    </div>
    <div className="table-wrap"><table>
      <thead><tr><th>Risk</th><th>Agent</th><th>Shift Date</th><th>Rule</th><th>Confidence</th><th>Reason</th></tr></thead>
      <tbody>{visible.map(x=><tr key={x.id} onClick={()=>navigate(`/findings/${x.id}`)} className="clickable">
        <td><span className={severityClass(x.severity)}>{x.severity}</span></td><td>{x.agent_id||"—"}</td><td>{x.shift_date||"—"}</td><td><code>{x.rule_id}</code></td><td>{Math.round(x.confidence*100)}%</td><td className="reason">{x.reason}</td>
      </tr>)}</tbody>
    </table>{!visible.length && <Empty text="No findings match the current filter."/>}</div>
  </>;
}

function FindingDetail() {
  const {id}=useParams(); const [d,setD]=useState<any>(null);
  useEffect(()=>{ if(id) api.finding(id).then(setD); },[id]);
  if(!d) return <Loading/>;
  const evidence=d.evidence?.evidence || [];
  return <>
    <PageHead title={`${d.rule_id} Finding`} sub="Immutable analytical evidence retained from the scan that generated this result."/>
    <div className="detail-grid">
      <section className="panel"><h2>Finding</h2>
        <dl><dt>Severity</dt><dd><span className={severityClass(d.severity)}>{d.severity}</span></dd><dt>Agent</dt><dd>{d.agent_id||"—"}</dd><dt>Shift Date</dt><dd>{d.shift_date||"—"}</dd><dt>Session</dt><dd>{d.session_id||"—"}</dd><dt>Confidence</dt><dd>{Math.round(d.confidence*100)}%</dd><dt>Risk Contribution</dt><dd>{d.risk_contribution}</dd></dl>
        <div className="callout">{d.reason}</div>
      </section>
      <section className="panel"><h2>Chain of Custody</h2><dl><dt>Scan</dt><dd className="mono">{d.scan_id}</dd><dt>Evidence Hash</dt><dd className="mono hash">{d.immutable_hash}</dd><dt>Rule</dt><dd>{d.evidence?.rule_name||d.rule_id}</dd><dt>Category</dt><dd>{d.evidence?.category||"—"}</dd></dl></section>
    </div>
    <HistoricalDecisionEvidence finding={d}/>
    <section className="panel"><div className="panel-title"><h2>Evidence</h2><span>{evidence.length} item(s)</span></div>
      {evidence.length ? <div className="evidence-list">{evidence.map((e:any,i:number)=><article key={i}><header><strong>{e.evidence_kind||"evidence"}</strong><span>{e.change_type||""}</span></header><p>{e.description}</p><div className="evidence-meta"><span>{e.baseline_source||"—"} → {e.comparison_source||"—"}</span><span>Δ {e.seconds_delta ?? 0}s</span><span>confidence {Math.round((e.confidence||0)*100)}%</span></div></article>)}</div> : <Empty text="This finding contains structured metadata but no attached activity evidence objects."/>}
    </section>
  </>;
}

function CasesPage() {
  const [rows,setRows]=useState<CaseRow[]>([]); const nav=useNavigate();
  useEffect(()=>{api.cases().then(setRows)},[]);
  return <>
    <PageHead title="Investigation Queue" sub="Human review workflow. Cases reference immutable findings without modifying analytical evidence."/>
    <div className="table-wrap"><table><thead><tr><th>Case</th><th>Title</th><th>Status</th><th>Disposition</th><th>Assigned</th><th>Updated</th></tr></thead>
    <tbody>{rows.map(x=><tr key={x.id} className="clickable" onClick={()=>nav(`/cases/${x.id}`)}><td><strong>{x.case_number}</strong></td><td>{x.title}</td><td><span className="badge neutral">{x.status}</span></td><td>{x.disposition}</td><td>{x.assigned_to||"Unassigned"}</td><td>{new Date(x.updated_at).toLocaleString()}</td></tr>)}</tbody></table>
    {!rows.length && <Empty text="No investigation cases have been created."/>}</div>
  </>;
}

function CaseDetail() {
  const {id}=useParams(); const [c,setC]=useState<CaseRow|null>(null); const [audit,setAudit]=useState<any[]>([]); const [note,setNote]=useState(""); const [ai,setAi]=useState<any>(null); const [aiBusy,setAiBusy]=useState(false);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const updating=useRef(false);
  const [linkedFindings,setLinkedFindings]=useState<any[]>([]);
  const load=async()=>{
    if(!id)return;
    setError("");
    try {
      const [detail,history,findings]=await Promise.all([api.caseDetail(id),api.caseAudit(id),api.caseFindings(id)]);
      setC(detail);setAudit(history);setLinkedFindings(findings);
      api.aiSummary(id).then(setAi).catch(()=>setAi(null));
    } catch(e) {setError(e instanceof Error ? e.message : "Could not load this case.")}
  };
  useEffect(()=>{setC(null);setAudit([]);setAi(null);setLinkedFindings([]);void load()},[id]);
  if(!c) return error ? <div role="alert"><ErrorBox text={error}/><button onClick={()=>void load()}>Retry loading case</button></div> : <Loading/>;
  const update=async(status:string)=>{
    if(!id || updating.current)return;
    updating.current=true;
    setBusy(true);setError("");
    try {await api.updateCase(id,{status,note:note||undefined});setNote("");await load()}
    catch(e){setError(e instanceof Error ? e.message : "Could not update this case.")}
    finally{updating.current=false;setBusy(false)}
  };
  const generate=async()=>{
    if(!id)return;setAiBusy(true);setError("");
    try{setAi(await api.generateAiSummary(id))}
    catch(e){setError(e instanceof Error ? e.message : "Could not generate the brief.")}
    finally{setAiBusy(false)}
  };
  return <>
    <PageHead title={c.case_number} sub={c.title}/>
    {error && <div role="alert"><ErrorBox text={error}/><button onClick={()=>void load()}>Reload case</button></div>}
    <div className="detail-grid">
      <section className="panel"><h2>Case Workflow</h2><dl><dt>Status</dt><dd>{c.status}</dd><dt>Disposition</dt><dd>{c.disposition}</dd><dt>Assigned To</dt><dd>{c.assigned_to||"Unassigned"}</dd><dt>Created By</dt><dd>{c.created_by}</dd></dl>
        <textarea aria-label="Reviewer note" disabled={busy} placeholder="Reviewer note…" value={note} onChange={e=>setNote(e.target.value)}/>
        <div className="actions" aria-busy={busy}>{c.status==="open"&&<button disabled={busy} onClick={()=>update("in_review")}>Start Review</button>}{c.status==="in_review"&&<><button disabled={busy} onClick={()=>update("awaiting_info")}>Request Information</button><button disabled={busy} onClick={()=>update("resolved")}>Resolve</button></>}{c.status==="awaiting_info"&&<button disabled={busy} onClick={()=>update("in_review")}>Resume Review</button>}{c.status==="resolved"&&<button disabled={busy} onClick={()=>update("closed")}>Close Case</button>}</div>
      </section>
      <section className="panel"><div className="panel-title"><h2>Audit History</h2><span>{audit.length} events</span></div><div className="audit">{audit.map((a,i)=><div key={a.id||i}><b>{a.event_type}</b><span>{a.actor}</span><small>{new Date(a.created_at).toLocaleString()}</small>{a.event_json?.before && a.event_json?.after && <p>{a.event_json.before.status} → {a.event_json.after.status}</p>}<p>{a.event_json?.note||""}</p></div>)}</div></section>
    </div>
    <section className="panel"><div className="panel-title"><h2>Linked Findings</h2><span>{linkedFindings.length} finding(s)</span></div>
      {!linkedFindings.length && <Empty text="No findings are linked to this case."/>}
      {linkedFindings.map(f=><article className="linked-finding" key={f.id}>
        <h3><NavLink to={`/findings/${f.id}`}>{f.rule_id} · Session {f.source_session_id || "Not recorded"}</NavLink></h3>
        <p>{f.reason}</p>
        <HistoricalDecisionEvidence finding={f}/>
        <details><summary>Finding provenance</summary><dl>
          <dt>Finding ID</dt><dd className="mono hash">{f.id}</dd>
          <dt>Scan ID</dt><dd className="mono hash">{f.scan_id}</dd>
          <dt>Immutable finding hash</dt><dd className="mono hash">{f.immutable_hash}</dd>
        </dl></details>
      </article>)}
    </section>
    <section className="panel"><div className="panel-title"><h2>AI Investigator Brief</h2><span>{ai ? `${ai.provider} · ${ai.model}` : "Evidence-grounded summary"}</span></div>
      <button onClick={generate} disabled={aiBusy}>{aiBusy ? "Generating…" : ai ? "Regenerate Brief" : "Generate Investigator Brief"}</button>
      {ai ? <div className="ai-brief"><pre>{ai.narrative}</pre><small>Prompt {ai.prompt_version} · Evidence input hash {ai.input_hash}</small></div> : <p className="muted">No AI brief has been generated. The AI layer summarizes existing findings only; it does not create or alter fraud evidence.</p>}
    </section>
  </>;
}

function ScansPage() {
  const [rows,setRows]=useState<ScanRow[]>([]);
  useEffect(()=>{api.scans().then(setRows)},[]);
  return <>
    <PageHead title="Scan Operations" sub="Durable scan execution, chunk progress, finalization and failure visibility."/>
    <div className="table-wrap"><table><thead><tr><th>Range</th><th>Status</th><th>Finalization</th><th>Employee-days</th><th>Findings</th><th>Chunks</th><th>Failures</th></tr></thead>
    <tbody>{rows.map(x=><tr key={x.id}><td>{x.date_from} → {x.date_to}</td><td><span className="badge neutral">{x.status}</span></td><td>{x.finalization_status}</td><td>{x.employee_days_processed}</td><td>{x.finding_count}</td><td><Progress done={x.completed_chunks} total={x.total_chunks}/></td><td>{x.failed_chunks}</td></tr>)}</tbody></table></div>
  </>;
}

function Progress({done,total}:{done:number;total:number}){const pct=total?Math.round(done*100/total):0;return <div className="progress"><span><i style={{width:`${pct}%`}}/></span><b>{done}/{total}</b></div>}
function Loading(){return <div className="state">Loading Sentinel data…</div>}
function ErrorBox({text}:{text:string}){return <div className="error">{text}</div>}
function Empty({text}:{text:string}){return <div className="empty">{text}</div>}

export default function App() {
  const [token,setToken]=useState(()=>sessionStorage.getItem("sentinel_access_token")||"");
  const [draft,setDraft]=useState("");
  const [authError,setAuthError]=useState("");
  useEffect(()=>{
    const expired=()=>{setToken("");setDraft("");setAuthError("Your session expired or the token is invalid. Enter a fresh token.")};
    window.addEventListener("sentinel:unauthorized",expired);
    return ()=>window.removeEventListener("sentinel:unauthorized",expired);
  },[]);
  if(!token) return <div className="auth-screen"><div className="auth-card"><div className="mark">S</div><h1>Sentinel AI</h1><p>Paste an enterprise access token or a locally generated development token.</p>{authError && <div role="alert"><ErrorBox text={authError}/></div>}<textarea value={draft} onChange={e=>setDraft(e.target.value)} placeholder="Bearer token value"/><button onClick={()=>{const v=draft.trim().replace(/^Bearer\s+/i, "");if(v){setAuthError("");sessionStorage.setItem("sentinel_access_token",v);setToken(v)}}}>Continue</button><small>Sentinel does not provide password authentication. Production identity should come from enterprise SSO/OIDC.</small></div></div>;
  return <Shell><Routes>
    <Route path="/" element={<OverviewPage/>}/>
    <Route path="/findings" element={<FindingsPage/>}/>
    <Route path="/findings/:id" element={<FindingDetail/>}/>
    <Route path="/cases" element={<CasesPage/>}/>
    <Route path="/cases/:id" element={<CaseDetail/>}/>
    <Route path="/scans" element={<ScansPage/>}/>
  </Routes></Shell>;
}

type RecordValue = Record<string, unknown>;

function record(value: unknown): RecordValue {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as RecordValue : {};
}

function display(value: unknown): string {
  return typeof value === "string" || typeof value === "number"
    ? String(value) : "Not recorded";
}

function managerDecision(value: unknown): string {
  if (value === 4) return "Accepted by Manager (4)";
  if (value === 5) return "Rejected by Manager (5)";
  return value == null ? "Not recorded" : `Unsupported decision (${display(value)})`;
}

export function HistoricalDecisionEvidence({finding}: {finding: RecordValue}) {
  if (finding.rule_id !== "QF-001") return null;
  const evidence = record(finding.evidence_json ?? finding.evidence);
  const metadata = record(evidence.metadata);
  const context = record(evidence.comparison_context);
  const earlier = record(metadata.earlier);
  const later = record(metadata.later);
  const reconciliations = record(context.reconciliation_statuses);
  const limitations = Array.isArray(context.reconciliation_limitations)
    ? context.reconciliation_limitations.filter((v): v is string => typeof v === "string") : [];
  const rows: [string, unknown, unknown][] = [
    ["Manager decision", managerDecision(earlier.supervisor_status_id), managerDecision(later.supervisor_status_id)],
    ["Session status (separate field)", earlier.status_id, later.status_id],
    ["Agent", earlier.agent_id, later.agent_id],
    ["Shift date", earlier.shift_date, later.shift_date],
    ["Observed at (UTC)", earlier.observed_at, later.observed_at],
    ["Manager action timestamp (UTC)", earlier.manager_action_at, later.manager_action_at],
    ["Run reconciliation", reconciliations[display(earlier.ingestion_run_id)], reconciliations[display(later.ingestion_run_id)]],
  ];
  return <section className="historical-evidence" aria-label="Manager decision comparison">
    <h3>Manager Decision Comparison</h3>
    <p className="callout">Historical observation anomaly requiring human review. This comparison does not establish fraud, an unauthorized edit, or payroll finalization.</p>
    <div className="table-wrap comparison-table"><table>
      <caption>Stored observations for session {display(finding.source_session_id ?? finding.session_id)}</caption>
      <thead><tr><th scope="col">Evidence</th><th scope="col">Earlier observation</th><th scope="col">Later observation</th></tr></thead>
      <tbody>{rows.map(([label,oldValue,newValue])=><tr key={label}>
        <th scope="row">{label}</th><td>{display(oldValue)}</td><td>{display(newValue)}</td>
      </tr>)}</tbody>
    </table></div>
    <div className="comparison-limits">
      <h4>Comparison Scope and Limitations</h4>
      <dl><dt>Eligibility mode</dt><dd>{display(context.eligibility_mode)}</dd>
        <dt>Authorized by</dt><dd>{display(context.override_actor)}</dd>
        <dt>Override reason</dt><dd>{display(context.override_reason)}</dd>
        <dt>Editor identity</dt><dd>{display(metadata.editor_identity)}</dd>
        <dt>Payroll finalization</dt><dd>{display(metadata.payroll_finalization)}</dd>
        <dt>Financial impact</dt><dd>{display(metadata.financial_impact)}</dd>
      </dl>
      {limitations.length > 0 ? <ul>{limitations.map((item,i)=><li key={i}>{item}</li>)}</ul>
        : <p>No reconciliation limitation details were recorded in this finding.</p>}
    </div>
    <details><summary>Source snapshot references and hashes</summary>
      <div className="detail-grid">{[["Earlier",earlier],["Later",later]].map(([label,value])=>{
        const row = record(value);
        return <div key={String(label)}><h4>{String(label)} snapshot</h4><dl>
          <dt>Snapshot ID</dt><dd className="mono hash">{display(row.snapshot_id)}</dd>
          <dt>Ingestion run ID</dt><dd className="mono hash">{display(row.ingestion_run_id)}</dd>
          <dt>Content hash</dt><dd className="mono hash">{display(row.content_hash)}</dd>
        </dl></div>;
      })}</div>
    </details>
  </section>;
}

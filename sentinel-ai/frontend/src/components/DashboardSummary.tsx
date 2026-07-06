import type { InvestigationCase } from "../types";

export function DashboardSummary({ cases }: { cases: InvestigationCase[] }) {
  const critical = cases.filter((item) => item.priority === "critical").length;
  const high = cases.filter((item) => item.priority === "high").length;
  const open = cases.filter((item) => item.status !== "closed").length;
  const avgRisk = cases.length
    ? Math.round(cases.reduce((sum, item) => sum + item.risk_score, 0) / cases.length)
    : 0;

  return (
    <div className="summary-grid">
      <div className="summary-card">
        <span>Open Cases</span>
        <strong>{open}</strong>
      </div>
      <div className="summary-card">
        <span>Critical</span>
        <strong>{critical}</strong>
      </div>
      <div className="summary-card">
        <span>High Risk</span>
        <strong>{high}</strong>
      </div>
      <div className="summary-card">
        <span>Avg Risk</span>
        <strong>{avgRisk}</strong>
      </div>
    </div>
  );
}

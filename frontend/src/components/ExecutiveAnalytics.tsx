import ReactECharts from "echarts-for-react";
import type { ExecutiveDashboardSummary } from "../dashboardTypes";

export function ExecutiveAnalytics({ data }: { data: ExecutiveDashboardSummary }) {
  const distributionOption = {
    tooltip: { trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["45%", "70%"],
        data: [
          { value: data.risk_distribution.normal, name: "Normal" },
          { value: data.risk_distribution.review, name: "Review" },
          { value: data.risk_distribution.suspicious, name: "Suspicious" },
          { value: data.risk_distribution.high_risk, name: "High Risk" },
          { value: data.risk_distribution.critical, name: "Critical" }
        ]
      }
    ]
  };

  const trendOption = {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: data.trend.map((item) => item.period) },
    yAxis: { type: "value" },
    series: [
      {
        name: "Cases",
        type: "bar",
        data: data.trend.map((item) => item.case_count)
      },
      {
        name: "Avg Risk",
        type: "line",
        data: data.trend.map((item) => item.average_risk_score)
      }
    ]
  };

  return (
    <section className="executive-panel">
      <div className="executive-header">
        <div>
          <h2>Executive Analytics</h2>
          <p>Leadership-level integrity risk overview.</p>
        </div>
      </div>

      <div className="executive-kpis">
        <div><span>Total Cases</span><strong>{data.total_cases}</strong></div>
        <div><span>Open Cases</span><strong>{data.open_cases}</strong></div>
        <div><span>Critical</span><strong>{data.critical_cases}</strong></div>
        <div><span>Avg Risk</span><strong>{data.average_risk_score}</strong></div>
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Risk Distribution</h3>
          <ReactECharts option={distributionOption} style={{ height: 260 }} />
        </div>
        <div className="chart-card">
          <h3>Case Volume & Risk Trend</h3>
          <ReactECharts option={trendOption} style={{ height: 260 }} />
        </div>
      </div>

      <div className="top-entities">
        <h3>Top Risk Entities</h3>
        {data.top_entities.map((item) => (
          <div key={`${item.entity_type}-${item.entity_id}`} className="top-entity-row">
            <span>{item.entity_type}: {item.entity_id}</span>
            <strong>{item.risk_score}/100</strong>
            <small>{item.case_count} case(s)</small>
          </div>
        ))}
      </div>
    </section>
  );
}

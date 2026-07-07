import type { ExecutiveDashboardSummary } from "./dashboardTypes";

export const mockExecutiveDashboard: ExecutiveDashboardSummary = {
  total_cases: 42,
  open_cases: 27,
  critical_cases: 8,
  high_risk_cases: 13,
  average_risk_score: 67.4,
  risk_distribution: {
    normal: 3,
    review: 5,
    suspicious: 13,
    high_risk: 13,
    critical: 8
  },
  trend: [
    { period: "2026-03", case_count: 8, average_risk_score: 42 },
    { period: "2026-04", case_count: 11, average_risk_score: 51 },
    { period: "2026-05", case_count: 16, average_risk_score: 59 },
    { period: "2026-06", case_count: 22, average_risk_score: 67 },
    { period: "2026-07", case_count: 27, average_risk_score: 71 }
  ],
  top_entities: [
    { entity_type: "agent", entity_id: "A-2381", risk_score: 94, case_count: 7 },
    { entity_type: "supervisor", entity_id: "S-104", risk_score: 91, case_count: 5 },
    { entity_type: "site", entity_id: "LHR-01", risk_score: 86, case_count: 12 },
    { entity_type: "campaign", entity_id: "Retail", risk_score: 79, case_count: 9 }
  ]
};

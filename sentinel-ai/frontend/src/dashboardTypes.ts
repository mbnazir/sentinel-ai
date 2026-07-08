export interface RiskDistribution {
  normal: number;
  review: number;
  suspicious: number;
  high_risk: number;
  critical: number;
}

export interface TrendPoint {
  period: string;
  case_count: number;
  average_risk_score: number;
}

export interface TopRiskEntity {
  entity_type: string;
  entity_id: string;
  risk_score: number;
  case_count: number;
}

export interface ExecutiveDashboardSummary {
  total_cases: number;
  open_cases: number;
  critical_cases: number;
  high_risk_cases: number;
  average_risk_score: number;
  risk_distribution: RiskDistribution;
  trend: TrendPoint[];
  top_entities: TopRiskEntity[];
}

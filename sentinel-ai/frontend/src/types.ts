export type InvestigationStatus =
  | "new"
  | "triaged"
  | "assigned"
  | "in_review"
  | "needs_more_info"
  | "substantiated"
  | "unsubstantiated"
  | "closed";

export type InvestigationPriority = "low" | "medium" | "high" | "critical";

export interface EvidenceLink {
  evidence_id: string;
  evidence_type: string;
  source: string;
  summary: string;
}

export interface InvestigationComment {
  author_id: string;
  body: string;
  created_at: string;
}

export interface InvestigationCase {
  case_id: string;
  organization_id: string;
  title: string;
  entity_type: string;
  entity_id: string;
  risk_score: number;
  priority: InvestigationPriority;
  status: InvestigationStatus;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
  summary: string;
  evidence_links: EvidenceLink[];
  comments: InvestigationComment[];
}

export interface InvestigationNarrative {
  case_id: string;
  executive_summary: string;
  key_findings: string[];
  evidence_summary: string[];
  recommended_next_steps: string[];
  limitations: string[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

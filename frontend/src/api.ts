export type Overview = {
  scan: null | {
    id: string; status: string; date_from: string; date_to: string;
    employee_days_processed: number; finding_count: number;
    total_chunks: number; completed_chunks: number; failed_chunks: number;
    engine_version?: string; rule_version?: string;
  };
  kpis: { total_findings: number; critical_findings: number; high_findings: number; open_cases: number };
  severity_distribution: Record<string, number>;
  top_rules: { rule_id: string; count: number }[];
  top_agents: { agent_id: string; risk_points: number }[];
};

export type Finding = {
  id: string; agent_id?: string; shift_date?: string; session_id?: string;
  rule_id: string; severity: string; confidence: number; risk_contribution: number; reason: string;
};
export type CaseRow = {
  id: string; case_number: string; title: string; status: string; disposition: string;
  assigned_to?: string; created_by: string; created_at: string; updated_at: string;
};
export type ScanRow = {
  id: string; status: string; date_from: string; date_to: string;
  employee_days_processed: number; finding_count: number; total_chunks: number;
  completed_chunks: number; failed_chunks: number; finalization_status: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = sessionStorage.getItem("sentinel_access_token");
  const r = await fetch(path, { headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init?.headers || {}) }, ...init });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export const api = {
  overview: (scanId?: string) => request<Overview>(`/api/v1/dashboard/overview${scanId ? `?scan_id=${scanId}` : ""}`),
  findings: (scanId: string) => request<Finding[]>(`/api/v1/dashboard/findings?scan_id=${scanId}`),
  finding: (id: string) => request<any>(`/api/v1/dashboard/findings/${id}`),
  cases: () => request<CaseRow[]>("/api/v1/dashboard/cases"),
  scans: () => request<ScanRow[]>("/api/v1/dashboard/scans"),
  caseDetail: (id: string) => request<CaseRow>(`/api/v1/investigations/${id}`),
  caseAudit: (id: string) => request<any[]>(`/api/v1/investigations/${id}/audit`),
  updateCase: (id: string, body: object) => request<CaseRow>(`/api/v1/investigations/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  aiSummary: (id: string) => request<any>(`/api/v1/ai/investigations/${id}/summary`),
  generateAiSummary: (id: string) => request<any>(`/api/v1/ai/investigations/${id}/summary`, { method: "POST" })
};

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
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);
  try {
    const r = await fetch(path, { ...init, headers, signal: controller.signal });
    if (r.status === 401) {
      sessionStorage.removeItem("sentinel_access_token");
      window.dispatchEvent(new Event("sentinel:unauthorized"));
      throw new Error("Your session expired or the token is invalid. Enter a fresh token.");
    }
    if (!r.ok) {
      if (r.status === 502 || r.status === 503 || r.status === 504) {
        throw new Error(`API unavailable (HTTP ${r.status}). Check the API and frontend containers, then retry.`);
      }
      throw new Error(`HTTP ${r.status}: ${await r.text()}`);
    }
    return await r.json();
  } catch (error) {
    if (controller.signal.aborted) throw new Error("The API request timed out. Please retry.");
    if (error instanceof TypeError) throw new Error("Cannot reach the API. Check connectivity, then retry.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  overview: (scanId?: string) => request<Overview>(`/api/v1/dashboard/overview${scanId ? `?scan_id=${scanId}` : ""}`),
  findings: (scanId: string) => request<Finding[]>(`/api/v1/dashboard/findings?scan_id=${scanId}`),
  finding: (id: string) => request<any>(`/api/v1/dashboard/findings/${id}`),
  cases: () => request<CaseRow[]>("/api/v1/dashboard/cases"),
  scans: () => request<ScanRow[]>("/api/v1/dashboard/scans"),
  caseDetail: (id: string) => request<CaseRow>(`/api/v1/investigations/${id}`),
  caseAudit: (id: string) => request<any[]>(`/api/v1/investigations/${id}/audit`),
  caseFindings: (id: string) => request<any[]>(`/api/v1/investigations/${id}/findings`),
  updateCase: (id: string, body: object) => request<CaseRow>(`/api/v1/investigations/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  aiSummary: (id: string) => request<any>(`/api/v1/ai/investigations/${id}/summary`),
  generateAiSummary: (id: string) => request<any>(`/api/v1/ai/investigations/${id}/summary`, { method: "POST" })
};

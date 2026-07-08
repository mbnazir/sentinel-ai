import type { InvestigationCase } from "./types";

export const mockCases: InvestigationCase[] = [
  {
    case_id: "SEN-DEMO-0001",
    organization_id: "ORG-1",
    title: "Critical integrity review for login_session LS-1001",
    entity_type: "login_session",
    entity_id: "LS-1001",
    risk_score: 92,
    priority: "critical",
    status: "new",
    assigned_to: null,
    created_at: "2026-07-06T10:00:00Z",
    updated_at: "2026-07-06T10:00:00Z",
    summary: "Supervisor and payroll activity extensions require review.",
    evidence_links: [
      {
        evidence_id: "E1",
        evidence_type: "extended_activity",
        source: "Extended Supervisor Activity",
        summary: "Supervisor extended a System activity by 45 minutes."
      },
      {
        evidence_id: "E2",
        evidence_type: "inserted_activity",
        source: "Inserted Payroll Activity",
        summary: "Payroll inserted an activity not present in System."
      }
    ],
    comments: []
  },
  {
    case_id: "SEN-DEMO-0002",
    organization_id: "ORG-1",
    title: "High risk review for agent A-2381",
    entity_type: "agent",
    entity_id: "A-2381",
    risk_score: 74,
    priority: "high",
    status: "assigned",
    assigned_to: "investigator-1",
    created_at: "2026-07-05T11:00:00Z",
    updated_at: "2026-07-05T12:00:00Z",
    summary: "Repeated manual additions over 90 days.",
    evidence_links: [
      {
        evidence_id: "E3",
        evidence_type: "behavior_profile",
        source: "Behavior Analytics",
        summary: "Agent manual added minutes are significantly above peer average."
      }
    ],
    comments: [
      {
        author_id: "investigator-1",
        body: "Initial review started.",
        created_at: "2026-07-05T12:00:00Z"
      }
    ]
  }
];

import type { TimelineVisualizationData } from "./timelineTypes";

export const mockTimelineByCase: Record<string, TimelineVisualizationData> = {
  "SEN-DEMO-0001": {
    case_id: "SEN-DEMO-0001",
    day_start: "2026-07-01T08:00:00Z",
    day_end: "2026-07-01T18:00:00Z",
    lanes: [
      {
        source: "System",
        activities: [
          {
            id: "SYS-1",
            source: "System",
            activity_type: "Work",
            start_time: "2026-07-01T08:00:00Z",
            end_time: "2026-07-01T12:00:00Z",
            duration_minutes: 240
          },
          {
            id: "SYS-2",
            source: "System",
            activity_type: "Lock / Idle",
            start_time: "2026-07-01T12:00:00Z",
            end_time: "2026-07-01T12:45:00Z",
            duration_minutes: 45,
            risk_type: "deleted",
            note: "This system idle block is absent in Supervisor/Payroll versions."
          },
          {
            id: "SYS-3",
            source: "System",
            activity_type: "Work",
            start_time: "2026-07-01T12:45:00Z",
            end_time: "2026-07-01T17:00:00Z",
            duration_minutes: 255
          }
        ]
      },
      {
        source: "Agent",
        activities: [
          {
            id: "AGT-1",
            source: "Agent",
            activity_type: "Work",
            start_time: "2026-07-01T08:00:00Z",
            end_time: "2026-07-01T12:00:00Z",
            duration_minutes: 240
          },
          {
            id: "AGT-2",
            source: "Agent",
            activity_type: "Work",
            start_time: "2026-07-01T12:45:00Z",
            end_time: "2026-07-01T17:00:00Z",
            duration_minutes: 255
          }
        ]
      },
      {
        source: "Supervisor",
        activities: [
          {
            id: "SUP-1",
            source: "Supervisor",
            activity_type: "Work",
            start_time: "2026-07-01T08:00:00Z",
            end_time: "2026-07-01T17:45:00Z",
            duration_minutes: 585,
            risk_type: "extended",
            note: "Supervisor extended payable work time by 45 minutes."
          }
        ]
      },
      {
        source: "Payroll",
        activities: [
          {
            id: "PAY-1",
            source: "Payroll",
            activity_type: "Work",
            start_time: "2026-07-01T08:00:00Z",
            end_time: "2026-07-01T17:45:00Z",
            duration_minutes: 585
          },
          {
            id: "PAY-2",
            source: "Payroll",
            activity_type: "Manual Adjustment",
            start_time: "2026-07-01T17:45:00Z",
            end_time: "2026-07-01T18:00:00Z",
            duration_minutes: 15,
            risk_type: "inserted",
            note: "Payroll inserted a manual payable adjustment."
          }
        ]
      }
    ],
    evidence: [
      {
        id: "EV-TL-1",
        title: "System idle time missing in later versions",
        severity: "high",
        description: "A 45-minute System idle/lock block is not represented in Supervisor or Payroll payable versions.",
        source: "System",
        activity_id: "SYS-2"
      },
      {
        id: "EV-TL-2",
        title: "Supervisor extended activity",
        severity: "critical",
        description: "Supervisor version extends payable time from 17:00 to 17:45.",
        source: "Supervisor",
        activity_id: "SUP-1"
      },
      {
        id: "EV-TL-3",
        title: "Payroll manual adjustment inserted",
        severity: "critical",
        description: "Payroll inserted an additional 15-minute manual adjustment after supervisor extension.",
        source: "Payroll",
        activity_id: "PAY-2"
      }
    ]
  }
};

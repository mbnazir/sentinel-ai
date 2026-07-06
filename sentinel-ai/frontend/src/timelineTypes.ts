export type TimelineSource = "Phone" | "System" | "Agent" | "Supervisor" | "Manager" | "Payroll";

export interface TimelineActivity {
  id: string;
  source: TimelineSource;
  activity_type: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  risk_type?: "normal" | "inserted" | "extended" | "deleted" | "type_changed" | "shifted";
  note?: string;
}

export interface TimelineLane {
  source: TimelineSource;
  activities: TimelineActivity[];
}

export interface TimelineEvidence {
  id: string;
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  source: TimelineSource;
  activity_id?: string;
}

export interface TimelineVisualizationData {
  case_id: string;
  day_start: string;
  day_end: string;
  lanes: TimelineLane[];
  evidence: TimelineEvidence[];
}

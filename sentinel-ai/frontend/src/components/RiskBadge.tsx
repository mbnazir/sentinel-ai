import type { InvestigationPriority } from "../types";

const labels: Record<InvestigationPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical"
};

export function RiskBadge({ priority }: { priority: InvestigationPriority }) {
  return <span className={`risk-badge risk-${priority}`}>{labels[priority]}</span>;
}

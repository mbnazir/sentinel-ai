import type { InvestigationStatus } from "../types";

export function StatusBadge({ status }: { status: InvestigationStatus }) {
  return <span className="status-badge">{status.replaceAll("_", " ")}</span>;
}

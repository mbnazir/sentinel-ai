import { AlertTriangle } from "lucide-react";
import type { InvestigationCase } from "../types";
import { RiskBadge } from "./RiskBadge";
import { StatusBadge } from "./StatusBadge";

interface Props {
  cases: InvestigationCase[];
  selectedCaseId: string | null;
  onSelect: (item: InvestigationCase) => void;
}

export function InvestigationQueue({ cases, selectedCaseId, onSelect }: Props) {
  return (
    <section className="queue">
      <div className="section-title">
        <AlertTriangle size={18} />
        Investigation Queue
      </div>

      {cases.map((item) => (
        <button
          key={item.case_id}
          className={`queue-item ${selectedCaseId === item.case_id ? "selected" : ""}`}
          onClick={() => onSelect(item)}
        >
          <div className="queue-row">
            <strong>{item.case_id}</strong>
            <RiskBadge priority={item.priority} />
          </div>
          <p>{item.title}</p>
          <div className="queue-row muted">
            <span>Score {item.risk_score}</span>
            <StatusBadge status={item.status} />
          </div>
        </button>
      ))}
    </section>
  );
}

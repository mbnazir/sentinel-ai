import { useState } from "react";
import type { InvestigationCase, InvestigationNarrative } from "../types";
import type { TimelineVisualizationData } from "../timelineTypes";
import { TimelineVisualization } from "./TimelineVisualization";
import { TimelineEvidencePanel } from "./TimelineEvidencePanel";
import { RiskBadge } from "./RiskBadge";
import { StatusBadge } from "./StatusBadge";

interface Props {
  selectedCase: InvestigationCase | null;
  narrative: InvestigationNarrative | null;
  onGenerateNarrative: () => void;
  timelineData: TimelineVisualizationData | null;
}

export function CaseDetail({ selectedCase, narrative, onGenerateNarrative, timelineData }: Props) {
  const [comment, setComment] = useState("");

  if (!selectedCase) {
    return <section className="case-detail empty">Select a case to review.</section>;
  }

  return (
    <section className="case-detail">
      <div className="case-header">
        <div>
          <h2>{selectedCase.title}</h2>
          <p className="muted">
            {selectedCase.entity_type} · {selectedCase.entity_id}
          </p>
        </div>
        <div className="case-actions">
          <RiskBadge priority={selectedCase.priority} />
          <StatusBadge status={selectedCase.status} />
        </div>
      </div>

      <div className="score-card">
        <span>Risk Score</span>
        <strong>{selectedCase.risk_score}/100</strong>
      </div>

      <h3>Summary</h3>
      <p>{selectedCase.summary}</p>

      <TimelineVisualization data={timelineData} />

      <TimelineEvidencePanel evidence={timelineData?.evidence ?? []} />

      <h3>Evidence</h3>
      <div className="evidence-list">
        {selectedCase.evidence_links.map((evidence) => (
          <div key={evidence.evidence_id} className="evidence-card">
            <strong>{evidence.source}</strong>
            <span>{evidence.evidence_type}</span>
            <p>{evidence.summary}</p>
          </div>
        ))}
      </div>

      <h3>AI Narrative</h3>
      <button className="primary-button" onClick={onGenerateNarrative}>
        Generate Evidence Narrative
      </button>

      {narrative && (
        <div className="narrative">
          <h4>Executive Summary</h4>
          <p>{narrative.executive_summary}</p>

          <h4>Key Findings</h4>
          <ul>{narrative.key_findings.map((item) => <li key={item}>{item}</li>)}</ul>

          <h4>Recommended Next Steps</h4>
          <ul>{narrative.recommended_next_steps.map((item) => <li key={item}>{item}</li>)}</ul>

          <h4>Limitations</h4>
          <ul>{narrative.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      )}

      <h3>Comments</h3>
      <div className="comments">
        {selectedCase.comments.map((item, index) => (
          <div key={`${item.created_at}-${index}`} className="comment">
            <strong>{item.author_id}</strong>
            <p>{item.body}</p>
          </div>
        ))}
      </div>

      <textarea
        value={comment}
        onChange={(event) => setComment(event.target.value)}
        placeholder="Add investigation note..."
      />
      <button className="secondary-button" disabled={!comment.trim()}>
        Add Comment
      </button>
    </section>
  );
}

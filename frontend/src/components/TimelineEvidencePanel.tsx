import type { TimelineEvidence } from "../timelineTypes";

export function TimelineEvidencePanel({ evidence }: { evidence: TimelineEvidence[] }) {
  if (!evidence.length) {
    return <div className="timeline-evidence empty">No timeline-specific evidence available.</div>;
  }

  return (
    <div className="timeline-evidence">
      <h3>Timeline Findings</h3>
      {evidence.map((item) => (
        <article key={item.id} className={`timeline-evidence-card severity-${item.severity}`}>
          <div>
            <strong>{item.title}</strong>
            <span>{item.source} · {item.severity}</span>
          </div>
          <p>{item.description}</p>
        </article>
      ))}
    </div>
  );
}

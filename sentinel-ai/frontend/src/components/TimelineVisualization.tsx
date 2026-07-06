import type { TimelineActivity, TimelineVisualizationData } from "../timelineTypes";

interface Props {
  data: TimelineVisualizationData | null;
}

const laneOrder = ["Phone", "System", "Agent", "Supervisor", "Manager", "Payroll"];

function minutesBetween(start: string, end: string): number {
  return (new Date(end).getTime() - new Date(start).getTime()) / 60000;
}

function activityStyle(activity: TimelineActivity, dayStart: string, dayEnd: string) {
  const totalMinutes = minutesBetween(dayStart, dayEnd);
  const left = (minutesBetween(dayStart, activity.start_time) / totalMinutes) * 100;
  const width = (activity.duration_minutes / totalMinutes) * 100;

  return {
    left: `${Math.max(0, left)}%`,
    width: `${Math.max(1, width)}%`
  };
}

export function TimelineVisualization({ data }: Props) {
  if (!data) {
    return <section className="timeline-panel empty">No timeline evidence available for this case yet.</section>;
  }

  const lanes = [...data.lanes].sort(
    (a, b) => laneOrder.indexOf(a.source) - laneOrder.indexOf(b.source)
  );

  return (
    <section className="timeline-panel">
      <div className="timeline-header">
        <h3>Activity Timeline Evidence</h3>
        <span>
          {new Date(data.day_start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -
          {" "}
          {new Date(data.day_end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>

      <div className="timeline-grid">
        {lanes.map((lane) => (
          <div key={lane.source} className="timeline-lane">
            <div className="lane-label">{lane.source}</div>
            <div className="lane-track">
              {lane.activities.map((activity) => (
                <div
                  key={activity.id}
                  className={`timeline-activity activity-${activity.risk_type ?? "normal"}`}
                  style={activityStyle(activity, data.day_start, data.day_end)}
                  title={`${activity.activity_type}: ${activity.duration_minutes} minutes`}
                >
                  <span>{activity.activity_type}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="timeline-legend">
        <span><i className="legend-normal" /> Normal</span>
        <span><i className="legend-extended" /> Extended</span>
        <span><i className="legend-inserted" /> Inserted</span>
        <span><i className="legend-deleted" /> Deleted / Missing</span>
        <span><i className="legend-type_changed" /> Type Changed</span>
      </div>
    </section>
  );
}

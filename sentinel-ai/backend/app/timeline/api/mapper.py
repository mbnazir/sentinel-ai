from app.infrastructure.persistence.models_timeline import NormalizedTimelineActivityModel


def source_label(data_source_id: int) -> str:
    return {
        0: "Phone",
        1: "System",
        2: "Agent",
        3: "Supervisor",
        4: "Manager",
        5: "Payroll",
    }.get(data_source_id, "Unknown")


def activity_to_frontend(activity: NormalizedTimelineActivityModel) -> dict:
    duration_minutes = round(activity.duration_seconds / 60, 2)

    return {
        "id": activity.external_id,
        "source": activity.source_label or source_label(activity.data_source_id),
        "activity_type": activity.activity_type_label,
        "start_time": activity.start_time.isoformat(),
        "end_time": activity.end_time.isoformat() if activity.end_time else activity.start_time.isoformat(),
        "duration_minutes": duration_minutes,
        "risk_type": activity.risk_type or "normal",
        "note": activity.risk_note,
    }


def build_timeline_visualization_response(
    login_session_external_id: str,
    activities: list[NormalizedTimelineActivityModel],
) -> dict:
    if not activities:
        return {
            "case_id": login_session_external_id,
            "day_start": "",
            "day_end": "",
            "lanes": [],
            "evidence": [],
        }

    closed = [activity for activity in activities if activity.end_time is not None]
    day_start = min(activity.start_time for activity in activities)
    day_end = max((activity.end_time or activity.start_time) for activity in activities)

    lanes_by_source: dict[str, list[dict]] = {}
    evidence = []

    for activity in activities:
        lane = activity.source_label or source_label(activity.data_source_id)
        lanes_by_source.setdefault(lane, []).append(activity_to_frontend(activity))

        if activity.risk_type and activity.risk_type != "normal":
            evidence.append(
                {
                    "id": f"TL-{activity.external_id}",
                    "title": f"{activity.risk_type.replace('_', ' ').title()} activity",
                    "severity": "critical" if activity.source_label in {"Manager", "Payroll"} else "high",
                    "description": activity.risk_note or "Activity contains a timeline risk marker.",
                    "source": lane,
                    "activity_id": activity.external_id,
                }
            )

    lane_order = ["Phone", "System", "Agent", "Supervisor", "Manager", "Payroll"]
    lanes = [
        {"source": source, "activities": lanes_by_source[source]}
        for source in lane_order
        if source in lanes_by_source
    ]

    return {
        "case_id": login_session_external_id,
        "day_start": day_start.isoformat(),
        "day_end": day_end.isoformat(),
        "lanes": lanes,
        "evidence": evidence,
    }

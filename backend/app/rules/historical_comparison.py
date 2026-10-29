"""Pure evaluators for explicitly selected historical snapshot comparisons."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import re
from uuid import UUID

from app.rules.models import FindingCategory, RuleFinding, RuleSeverity


@dataclass(frozen=True, slots=True)
class ManagerDecisionObservation:
    """Manager decision and provenance captured in one session snapshot."""

    snapshot_id: UUID | str
    ingestion_run_id: UUID | str
    source_system: str
    source_session_id: str
    status_id: int | None
    ready_for_payroll: bool
    observed_at: datetime
    manager_action_at: datetime | None
    agent_id: str
    shift_date: date | str
    content_hash: str
    content_hash_verified: bool = True
    # Quartz stores manager decisions in this workflow column, not status_id.
    supervisor_status_id: int | None = None


@dataclass(frozen=True, slots=True)
class ManagerDecisionComparison:
    findings: tuple[RuleFinding, ...]
    excluded_record_counts: dict[str, int]
    matched_pairs_count: int
    valid_comparisons_count: int
    excluded_pair_counts: dict[str, int]
    excluded_pair_session_ids: dict[str, tuple[str, ...]]


def _utc(value: datetime) -> datetime:
    """Normalize timestamps to UTC; naive persisted values are treated as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def evaluate_manager_decision_reversals_detailed(
    earlier: tuple[ManagerDecisionObservation, ...] | list[ManagerDecisionObservation],
    later: tuple[ManagerDecisionObservation, ...] | list[ManagerDecisionObservation],
    *,
    earlier_run_id: UUID | str | None = None,
    later_run_id: UUID | str | None = None,
) -> ManagerDecisionComparison:
    """Compare valid matched rows, excluding ambiguous evidence and reporting counts.

    Unmatched sessions are counted as non-comparable observations. Their absence is
    never interpreted as deletion.
    """
    earlier_run_ids = {str(row.ingestion_run_id) for row in earlier}
    later_run_ids = {str(row.ingestion_run_id) for row in later}
    selected_earlier = str(earlier_run_id) if earlier_run_id is not None else (
        next(iter(earlier_run_ids)) if len(earlier_run_ids) == 1 else None
    )
    selected_later = str(later_run_id) if later_run_id is not None else (
        next(iter(later_run_ids)) if len(later_run_ids) == 1 else None
    )
    excluded = {
        "invalid_identity_records": 0,
        "invalid_content_hash_records": 0,
        "content_hash_mismatch_records": 0,
        "invalid_timestamp_records": 0,
        "ambiguous_duplicate_records": 0,
        "unmatched_earlier_records": 0,
        "unmatched_later_records": 0,
        "non_payroll_ready_pair_records": 0,
        "unsupported_status_pair_records": 0,
        "unchanged_decision_pair_records": 0,
        "non_chronological_pair_records": 0,
        "conflicting_agent_identity_pair_records": 0,
        "archived_session_records": 0,
        "archived_session_counterpart_records": 0,
    }
    excluded_pairs = {
        "ambiguous_duplicate_keys": 0,
        "unmatched_earlier_records": 0,
        "unmatched_later_records": 0,
        "non_chronological_pairs": 0,
        "conflicting_agent_identity_pairs": 0,
        "archived_session_pairs": 0,
        "non_payroll_ready_pairs": 0,
        "unsupported_status_pairs": 0,
        "unchanged_decision_pairs": 0,
    }
    excluded_pair_ids: dict[str, list[str]] = {
        reason: [] for reason in excluded_pairs
    }
    if (
        selected_earlier is None
        or selected_later is None
        or (earlier_run_ids and earlier_run_ids != {selected_earlier})
        or (later_run_ids and later_run_ids != {selected_later})
        or selected_earlier == selected_later
    ):
        return ManagerDecisionComparison((), excluded, 0, 0, excluded_pairs, {})

    def valid_rows(rows):
        valid = []
        for row in rows:
            shift_is_valid = isinstance(row.shift_date, date) or (
                isinstance(row.shift_date, str)
                and re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.shift_date) is not None
            )
            if (
                not isinstance(row.snapshot_id, (str, UUID))
                or not str(row.snapshot_id).strip()
                or not isinstance(row.source_system, str)
                or not row.source_system.strip()
                or not isinstance(row.source_session_id, str)
                or not row.source_session_id.strip()
                or not isinstance(row.agent_id, str)
                or not row.agent_id.strip()
                or not shift_is_valid
                or not isinstance(row.ready_for_payroll, bool)
            ):
                excluded["invalid_identity_records"] += 1
                continue
            if not isinstance(row.content_hash, str) or re.fullmatch(
                r"[0-9a-fA-F]{64}", row.content_hash
            ) is None:
                excluded["invalid_content_hash_records"] += 1
                continue
            if not row.content_hash_verified:
                excluded["content_hash_mismatch_records"] += 1
                continue
            if not isinstance(row.observed_at, datetime):
                excluded["invalid_timestamp_records"] += 1
                continue
            try:
                _utc(row.observed_at)
                if row.manager_action_at is not None:
                    _utc(row.manager_action_at)
            except (OverflowError, ValueError, TypeError):
                excluded["invalid_timestamp_records"] += 1
                continue
            valid.append(row)
        return valid

    valid_earlier = valid_rows(earlier)
    valid_later = valid_rows(later)
    # Quartz uses agent_id="0" for archived sessions. If either observation
    # is archived, exclude the whole source/session key so its active counterpart
    # is not misreported as unmatched or as an employee identity change.
    archived_keys = {
        (row.source_system, row.source_session_id)
        for row in valid_earlier + valid_later
        if row.source_system == "quartz" and row.agent_id == "0"
    }
    earlier_keys = {(row.source_system, row.source_session_id) for row in valid_earlier}
    later_keys = {(row.source_system, row.source_session_id) for row in valid_later}
    archived_pair_keys = archived_keys & earlier_keys & later_keys
    excluded_pairs["archived_session_pairs"] = len(archived_pair_keys)
    excluded_pair_ids["archived_session_pairs"] = [
        key[1] for key in sorted(archived_pair_keys)
    ]

    def active_rows(rows):
        active = []
        for row in rows:
            if (row.source_system, row.source_session_id) in archived_keys:
                reason = ("archived_session_records" if row.agent_id == "0"
                          else "archived_session_counterpart_records")
                excluded[reason] += 1
            else:
                active.append(row)
        return active

    valid_earlier = active_rows(valid_earlier)
    valid_later = active_rows(valid_later)
    earlier_grouped: dict[tuple[str, str], list[ManagerDecisionObservation]] = {}
    later_grouped: dict[tuple[str, str], list[ManagerDecisionObservation]] = {}
    for row in valid_earlier:
        earlier_grouped.setdefault((row.source_system, row.source_session_id), []).append(row)
    for row in valid_later:
        later_grouped.setdefault((row.source_system, row.source_session_id), []).append(row)

    duplicate_keys = {key for key, rows in earlier_grouped.items() if len(rows) != 1}
    duplicate_keys |= {key for key, rows in later_grouped.items() if len(rows) != 1}
    excluded["ambiguous_duplicate_records"] = sum(
        len(earlier_grouped.get(key, [])) + len(later_grouped.get(key, []))
        for key in duplicate_keys
    )
    excluded_pairs["ambiguous_duplicate_keys"] = len(duplicate_keys)
    excluded_pair_ids["ambiguous_duplicate_keys"] = [key[1] for key in sorted(duplicate_keys)]
    old_by_key = {
        key: rows[0] for key, rows in earlier_grouped.items()
        if len(rows) == 1 and key not in duplicate_keys
    }
    new_by_key = {
        key: rows[0] for key, rows in later_grouped.items()
        if len(rows) == 1 and key not in duplicate_keys
    }
    excluded["unmatched_earlier_records"] = len(old_by_key.keys() - new_by_key.keys())
    excluded["unmatched_later_records"] = len(new_by_key.keys() - old_by_key.keys())
    excluded_pairs["unmatched_earlier_records"] = excluded["unmatched_earlier_records"]
    excluded_pairs["unmatched_later_records"] = excluded["unmatched_later_records"]
    excluded_pair_ids["unmatched_earlier_records"] = sorted(
        key[1] for key in old_by_key.keys() - new_by_key.keys()
    )
    excluded_pair_ids["unmatched_later_records"] = sorted(
        key[1] for key in new_by_key.keys() - old_by_key.keys()
    )

    findings: list[RuleFinding] = []
    matched_keys = old_by_key.keys() & new_by_key.keys()
    valid_comparisons = 0
    for key in sorted(matched_keys):
        old, new = old_by_key[key], new_by_key[key]
        old_observed_at, new_observed_at = _utc(old.observed_at), _utc(new.observed_at)
        if new_observed_at <= old_observed_at:
            excluded["non_chronological_pair_records"] += 2
            excluded_pairs["non_chronological_pairs"] += 1
            excluded_pair_ids["non_chronological_pairs"].append(key[1])
            continue
        if old.agent_id != new.agent_id:
            excluded["conflicting_agent_identity_pair_records"] += 2
            excluded_pairs["conflicting_agent_identity_pairs"] += 1
            excluded_pair_ids["conflicting_agent_identity_pairs"].append(key[1])
            continue
        valid_comparisons += 1
        if not (old.ready_for_payroll and new.ready_for_payroll):
            excluded["non_payroll_ready_pair_records"] += 2
            excluded_pairs["non_payroll_ready_pairs"] += 1
            excluded_pair_ids["non_payroll_ready_pairs"].append(key[1])
            continue
        if old.supervisor_status_id not in (4, 5) or new.supervisor_status_id not in (4, 5):
            excluded["unsupported_status_pair_records"] += 2
            excluded_pairs["unsupported_status_pairs"] += 1
            excluded_pair_ids["unsupported_status_pairs"].append(key[1])
            continue
        if old.supervisor_status_id == new.supervisor_status_id:
            excluded["unchanged_decision_pair_records"] += 2
            excluded_pairs["unchanged_decision_pairs"] += 1
            excluded_pair_ids["unchanged_decision_pairs"].append(key[1])
            continue

        transition = f"{old.supervisor_status_id}->{new.supervisor_status_id}"
        identity = [
            "QF-001", old.source_system, old.source_session_id,
            selected_earlier, selected_later,
        ]
        finding_key = "QF-001:" + hashlib.sha256(
            json.dumps(identity, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        description = (
            f"Manager decision changed from {old.supervisor_status_id} "
            f"to {new.supervisor_status_id} between "
            "two payroll-ready historical observations. This is a historical observation "
            "anomaly for human review; it does not establish unauthorized access, payroll "
            "finalization, or fraud."
        )
        findings.append(RuleFinding(
            rule_id="QF-001",
            rule_name="Manager Decision Reversal",
            category=FindingCategory.WORKFLOW,
            severity=RuleSeverity.MEDIUM,
            source_session_id=old.source_session_id,
            confidence=0.65,
            risk_contribution=15.0,
            reason=description,
            metadata={
                "finding_key": finding_key,
                "source_system": old.source_system,
                "transition": transition,
                "decision_field": "supervisor_status_id",
                "classification": "HISTORICAL_OBSERVATION_ANOMALY",
                "observation": "Manager decision status changed between selected snapshots.",
                "interpretation": "Workflow anomaly requiring human review.",
                "risk": "Neither the editor identity nor an unauthorized action is established.",
                "financial_impact": "UNVERIFIED",
                "payroll_finalization": "UNVERIFIED",
                "earlier": {
                    "snapshot_id": str(old.snapshot_id),
                    "ingestion_run_id": selected_earlier,
                    "content_hash": old.content_hash,
                    "observed_at": old_observed_at.isoformat(),
                    "manager_action_at": _utc(old.manager_action_at).isoformat()
                    if old.manager_action_at else None,
                    "status_id": old.status_id,
                    "supervisor_status_id": old.supervisor_status_id,
                    "agent_id": old.agent_id,
                    "shift_date": old.shift_date.isoformat()
                    if isinstance(old.shift_date, date) else old.shift_date,
                },
                "later": {
                    "snapshot_id": str(new.snapshot_id),
                    "ingestion_run_id": selected_later,
                    "content_hash": new.content_hash,
                    "observed_at": new_observed_at.isoformat(),
                    "manager_action_at": _utc(new.manager_action_at).isoformat()
                    if new.manager_action_at else None,
                    "status_id": new.status_id,
                    "supervisor_status_id": new.supervisor_status_id,
                    "agent_id": new.agent_id,
                    "shift_date": new.shift_date.isoformat()
                    if isinstance(new.shift_date, date) else new.shift_date,
                },
                "editor_identity": "UNVERIFIED",
            },
        ))
    return ManagerDecisionComparison(
        tuple(findings), excluded, len(matched_keys), valid_comparisons, excluded_pairs,
        {reason: tuple(session_ids) for reason, session_ids in excluded_pair_ids.items()},
    )


def evaluate_manager_decision_reversals(
    earlier: tuple[ManagerDecisionObservation, ...] | list[ManagerDecisionObservation],
    later: tuple[ManagerDecisionObservation, ...] | list[ManagerDecisionObservation],
) -> tuple[RuleFinding, ...]:
    """Compatibility wrapper returning findings only."""
    return evaluate_manager_decision_reversals_detailed(earlier, later).findings

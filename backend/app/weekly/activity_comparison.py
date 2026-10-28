from datetime import UTC, datetime
from decimal import Decimal
from itertools import pairwise
from uuid import UUID

from app.weekly.activity_models import (
    ActivityChange,
    ActivityChangeType,
    ActivityInterval,
    ActivityVersion,
    ChangeEvidence,
    ComparisonReadiness,
    ComparisonStatus,
    VersionComparison,
)
from app.weekly.rules import evaluate_wf005


def _utc(value: datetime) -> tuple[datetime, bool]:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC), True
    return value.astimezone(UTC), False


def _seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return Decimal(delta.days * 86400 + delta.seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)


def _unique(values):
    return tuple(sorted(set(values)))


def _active(intervals: tuple[ActivityInterval, ...], start: datetime, end: datetime):
    return tuple(i for i in intervals if i.start_at < end and i.end_at is not None and i.end_at > start)


def _evidence(before, after) -> ChangeEvidence:
    return ChangeEvidence(
        original_activity_ids=_unique(i.activity_id for i in before),
        revised_activity_ids=_unique(i.activity_id for i in after),
        original_comments=_unique(i.comment for i in before if i.comment is not None),
        revised_comments=_unique(i.comment for i in after if i.comment is not None),
        original_created_at=_unique(i.source_created_at for i in before if i.source_created_at is not None),
        revised_created_at=_unique(i.source_created_at for i in after if i.source_created_at is not None),
        original_updated_at=_unique(i.source_updated_at for i in before if i.source_updated_at is not None),
        revised_updated_at=_unique(i.source_updated_at for i in after if i.source_updated_at is not None),
        editor_identity="UNVERIFIED", editor_identity_verified=False, financial_impact="UNVERIFIED",
        provenance=("Activity source ID identifies a representation, not an editor",
                    "Creation/update timestamps are preserved as evidence, not treated as edit time"),
    )


def compare_activity_versions(
    original: ActivityVersion | None,
    revised: ActivityVersion | None,
    *,
    ingestion_run_id: UUID,
    source_system: str,
    source_session_id: str,
    original_source_id: int | None = None,
    revised_source_id: int | None = None,
) -> VersionComparison:
    """Compare two source timelines by classifying atomic UTC intervals.

    Activity IDs identify evidence but never establish a change by themselves. Coverage is the
    union of intervals on each side, so overlapping rows cannot double count elapsed time.
    """
    reasons: list[str] = []
    missing_sources: list[int] = []
    malformed: list[str] = []
    mismatches: list[str] = []
    unsupported_source = False
    if original is None:
        if original_source_id is not None:
            missing_sources.append(original_source_id)
        reasons.append("Original source version is unavailable")
    if revised is None:
        if revised_source_id is not None:
            missing_sources.append(revised_source_id)
        reasons.append("Revised source version is unavailable")
    composite_key_mismatch = False
    for version in (original, revised):
        if version is None:
            continue
        if (version.ingestion_run_id != ingestion_run_id or version.source_system != source_system
                or version.source_session_id != source_session_id):
            reasons.append("Version does not match the requested ingestion/session composite key")
            composite_key_mismatch = True
        if version.data_source_id not in range(6):
            reasons.append(f"Unsupported source version ID {version.data_source_id}")
            unsupported_source = True
        for item in version.activities:
            if (item.ingestion_run_id != ingestion_run_id or item.source_system != source_system
                    or item.source_session_id != source_session_id
                    or item.data_source_id != version.data_source_id):
                reasons.append(f"Activity {item.activity_id} does not match its source-version composite key")
                composite_key_mismatch = True
    if composite_key_mismatch or unsupported_source:
        return VersionComparison(ingestion_run_id=ingestion_run_id, source_system=source_system,
            source_session_id=source_session_id, original_version=original, revised_version=revised,
            readiness=ComparisonReadiness(status=ComparisonStatus.INCOMPLETE,
                reasons=tuple(dict.fromkeys(reasons))), net_covered_seconds=None,
            reclassified_seconds=Decimal(0))

    normalized: list[tuple[ActivityInterval, ...]] = []
    naive_seen = False
    for version in (original, revised):
        rows: list[ActivityInterval] = []
        for item in version.activities if version else ():
            start, start_naive = _utc(item.start_at)
            end, end_naive = (_utc(item.end_at) if item.end_at is not None else (None, False))
            created, created_naive = (_utc(item.source_created_at) if item.source_created_at else (None, False))
            updated, updated_naive = (_utc(item.source_updated_at) if item.source_updated_at else (None, False))
            naive_seen |= start_naive or end_naive or created_naive or updated_naive
            rows.append(item.model_copy(update={"start_at": start, "end_at": end,
                "source_created_at": created, "source_updated_at": updated}))
            if end is None or end <= start:
                malformed.append(item.activity_id)
                reasons.append(f"Activity {item.activity_id} has an open-ended or invalid interval")
                continue
            if item.duration_seconds is not None and abs(item.duration_seconds - _seconds(start, end)) > Decimal(1):
                mismatches.append(item.activity_id)
                reasons.append(f"Activity {item.activity_id} duration disagrees materially with its timestamps")
        normalized.append(tuple(rows))
    if naive_seen:
        reasons.append("Naive timestamps were interpreted as UTC")

    before_rows, after_rows = normalized
    changes: list[ActivityChange] = []
    valid_before = tuple(i for i in before_rows if i.end_at is not None and i.end_at > i.start_at)
    valid_after = tuple(i for i in after_rows if i.end_at is not None and i.end_at > i.start_at)
    bounds = sorted({p for rows in (valid_before, valid_after) for i in rows
                     for p in (i.start_at, i.end_at) if p is not None})
    atoms: list[dict[str, object]] = []
    conflict_count = 0
    for start, end in pairwise(bounds):
        if end <= start:
            continue
        left, right = _active(valid_before, start, end), _active(valid_after, start, end)
        old_types, new_types = {i.activity_type_id for i in left}, {i.activity_type_id for i in right}
        if len(old_types) > 1 or len(new_types) > 1:
            kind = ActivityChangeType.AMBIGUOUS
            conflict_count += 1
        elif old_types and new_types:
            kind = (ActivityChangeType.UNCHANGED if old_types == new_types
                    else ActivityChangeType.RECLASSIFIED)
        elif old_types:
            kind = ActivityChangeType.REMOVED
        elif new_types:
            kind = ActivityChangeType.ADDED
        else:
            continue
        atoms.append({"start": start, "end": end, "kind": kind, "left": left, "right": right,
                      "old_types": tuple(sorted(old_types)), "new_types": tuple(sorted(new_types)),
                      "net": _seconds(start, end) * (int(bool(right)) - int(bool(left)))})

    # A one-sided edge touching same-type covered time on both versions is a boundary adjustment.
    for index, atom in enumerate(atoms):
        kind = atom["kind"]
        if kind not in {ActivityChangeType.ADDED, ActivityChangeType.REMOVED}:
            continue
        neighbors = atoms[max(0, index - 1): index] + atoms[index + 1:index + 2]
        for neighbor in neighbors:
            if not (neighbor["end"] == atom["start"] or neighbor["start"] == atom["end"]):
                continue
            if (neighbor["kind"] == ActivityChangeType.UNCHANGED
                    and (atom["new_types"] if kind == ActivityChangeType.ADDED else atom["old_types"])
                    == neighbor["old_types"] == neighbor["new_types"]):
                atom["kind"] = (ActivityChangeType.EXTENDED if kind == ActivityChangeType.ADDED
                                else ActivityChangeType.SHORTENED)
                break

    # Coalesce only adjacent atoms with identical semantics and evidence identities.
    groups: list[list[dict[str, object]]] = []
    for atom in atoms:
        if groups:
            previous = groups[-1][-1]
            same_evidence = (_unique(i.activity_id for i in previous["left"]) ==
                             _unique(i.activity_id for i in atom["left"]) and
                             _unique(i.activity_id for i in previous["right"]) ==
                             _unique(i.activity_id for i in atom["right"]))
            if (previous["end"] == atom["start"] and previous["kind"] == atom["kind"]
                    and previous["old_types"] == atom["old_types"]
                    and previous["new_types"] == atom["new_types"] and same_evidence):
                groups[-1].append(atom)
                continue
        groups.append([atom])
    for group in groups:
        first, last = group[0], group[-1]
        left = tuple({i.activity_id: i for atom in group for i in atom["left"]}.values())
        right = tuple({i.activity_id: i for atom in group for i in atom["right"]}.values())
        start, end = first["start"], last["end"]
        changes.append(ActivityChange(change_type=first["kind"], start_at=start, end_at=end,
            affected_seconds=_seconds(start, end), net_covered_seconds=sum((a["net"] for a in group), Decimal(0)),
            original_activity_ids=_unique(i.activity_id for i in left),
            revised_activity_ids=_unique(i.activity_id for i in right),
            original_activity_type_ids=first["old_types"], revised_activity_type_ids=first["new_types"],
            evidence=_evidence(left, right)))

    for item in malformed:
        source = next((i for i in (*before_rows, *after_rows) if i.activity_id == item), None)
        if source:
            is_old = source in before_rows
            changes.append(ActivityChange(change_type=ActivityChangeType.AMBIGUOUS,
                start_at=source.start_at, end_at=source.end_at, affected_seconds=None,
                net_covered_seconds=None,
                original_activity_ids=(item,) if is_old else (),
                revised_activity_ids=() if is_old else (item,),
                original_activity_type_ids=(source.activity_type_id,) if is_old else (),
                revised_activity_type_ids=() if is_old else (source.activity_type_id,),
                evidence=_evidence((source,) if is_old else (), () if is_old else (source,))))

    if conflict_count:
        reasons.append("Conflicting activity types overlap within at least one source version")
    if original and revised and original.data_source_id == revised.data_source_id:
        reasons.append("Compared versions use the same Quartz source ID")
    elif (original and revised
          and abs(original.data_source_id - revised.data_source_id) > 1):
        reasons.append("Pairwise comparison does not establish that intervening source versions are complete")
    if malformed or missing_sources or mismatches or conflict_count or reasons:
        status = ComparisonStatus.INCOMPLETE if missing_sources or malformed else ComparisonStatus.PROVISIONAL
    else:
        status = ComparisonStatus.READY
    net_covered = None if malformed or missing_sources else sum(
        (change.net_covered_seconds or Decimal(0) for change in changes), Decimal(0))
    reclassified = sum((change.affected_seconds or Decimal(0) for change in changes
                        if change.change_type == ActivityChangeType.RECLASSIFIED), Decimal(0))
    result = VersionComparison(ingestion_run_id=ingestion_run_id, source_system=source_system,
        source_session_id=source_session_id, original_version=original, revised_version=revised,
        changes=tuple(changes), readiness=ComparisonReadiness(status=status, reasons=tuple(dict.fromkeys(reasons)),
            missing_source_ids=tuple(missing_sources), malformed_activity_ids=_unique(malformed),
            conflicting_segments=conflict_count, duration_mismatch_activity_ids=_unique(mismatches)),
        net_covered_seconds=net_covered, reclassified_seconds=reclassified,
        evidence_confidence=None, finding=None)
    return result.model_copy(update={"finding": evaluate_wf005(result)})

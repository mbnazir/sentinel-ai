"""Add to backend/tests and run with pytest after applying changes."""
from datetime import date
from uuid import UUID, uuid4

from app.workers.tasks import _lock_key
from app.workers.chunking import split_date_range
from app.workers.pipeline import ENGINE_VERSION, RULE_VERSION


def test_scan_lock_key_is_deterministic_and_signed_bigint():
    scan = uuid4()
    assert _lock_key(scan) == _lock_key(UUID(str(scan)))
    assert -(2**63) <= _lock_key(scan) < 2**63


def test_distinct_scan_ids_use_distinct_sample_lock_keys():
    ids = [uuid4() for _ in range(100)]
    assert len({_lock_key(scan) for scan in ids}) == len(ids)


def test_chunk_boundaries_stable():
    scan = uuid4()
    a = split_date_range(scan, date(2026, 8, 1), date(2026, 8, 4), 1)
    b = split_date_range(scan, date(2026, 8, 1), date(2026, 8, 4), 1)
    assert [(x.chunk_index, x.date_from, x.date_to) for x in a] == [
        (x.chunk_index, x.date_from, x.date_to) for x in b
    ]


def test_rule_versions_unchanged():
    assert ENGINE_VERSION == "0.9.0"
    assert RULE_VERSION == "builtin-24-v1"

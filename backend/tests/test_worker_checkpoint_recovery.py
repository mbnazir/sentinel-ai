"""Isolated checkpoint recovery simulation; not a database integration test."""

from datetime import date

import pytest


class SimulatedWorkerFailure(RuntimeError):
    pass


def run_checkpointed_days(days, *, checkpoint, findings, fail_after=None):
    processed = checkpoint.get("processed", 0)

    for day in days[processed:]:
        findings.add("finding:" + day.isoformat())
        processed += 1
        checkpoint.update(
            {
                "version": 2,
                "last_shift_date": day.isoformat(),
                "processed": processed,
            }
        )
        if fail_after is not None and processed == fail_after:
            raise SimulatedWorkerFailure("Intentional test interruption")

    return processed


def test_checkpoint_resume_after_interruption():
    days = [date(2026, 8, day) for day in range(1, 11)]
    checkpoint = {}
    findings = set()

    with pytest.raises(SimulatedWorkerFailure):
        run_checkpointed_days(
            days,
            checkpoint=checkpoint,
            findings=findings,
            fail_after=3,
        )

    assert checkpoint["version"] == 2
    assert checkpoint["processed"] == 3
    assert len(findings) == 3

    processed = run_checkpointed_days(days, checkpoint=checkpoint, findings=findings)

    assert processed == 10
    assert checkpoint["processed"] == 10
    assert len(findings) == 10


def test_repeated_execution_does_not_duplicate_findings():
    days = [date(2026, 8, day) for day in range(1, 11)]
    checkpoint = {}
    findings = set()

    run_checkpointed_days(days, checkpoint=checkpoint, findings=findings)
    run_checkpointed_days(days, checkpoint=checkpoint, findings=findings)

    assert len(findings) == 10
    assert checkpoint["processed"] == 10

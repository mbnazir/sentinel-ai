"""One-shot, process-local fault injection for Sentinel AI checkpoint recovery UAT.

Run inside the existing API container. Does not change application source files.
"""
import asyncio
from uuid import UUID

import app.workers.tasks as tasks

SCAN_ID = UUID('ab2b3a2a-29ff-404c-975b-e2f70c92e4e7')
original_processor = tasks.process_employee_day
successful_calls = 0


class RecoveryUATInterruption(RuntimeError):
    pass


async def injected_processor(db, *, scan_id, ingestion_run_id, agent_id, shift_date):
    global successful_calls
    if scan_id == SCAN_ID and successful_calls == 3:
        raise RecoveryUATInterruption('Intentional interruption before employee-day 4')

    result = await original_processor(
        db,
        scan_id=scan_id,
        ingestion_run_id=ingestion_run_id,
        agent_id=agent_id,
        shift_date=shift_date,
    )
    if scan_id == SCAN_ID:
        successful_calls += 1
        print(f'Employee-day processor calls completed: {successful_calls}', flush=True)
    return result


async def main():
    tasks.process_employee_day = injected_processor
    try:
        await tasks._execute_scan(SCAN_ID, 'checkpoint-recovery-uat')
    except RecoveryUATInterruption as exc:
        assert successful_calls == 3, f'Expected 3 calls; got {successful_calls}'
        print(f'EXPECTED INTERRUPTION: {exc}', flush=True)
    else:
        raise AssertionError('Expected interruption was not raised')
    finally:
        tasks.process_employee_day = original_processor


if __name__ == '__main__':
    asyncio.run(main())

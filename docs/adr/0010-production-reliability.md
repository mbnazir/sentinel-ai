# ADR 0010: Separate execution reliability from analytical logic

Status: Accepted

Locks, throttling, retry policy, stale-job recovery, dead-letter behavior and operational metrics belong to infrastructure/reliability modules and must not leak into rule logic. Population finalization executes only after deterministic chunks are complete.

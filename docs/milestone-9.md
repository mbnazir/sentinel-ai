# Milestone 9 - Durable Chunk Execution and Full Scan Pipeline

Each scan now owns durable `scan_chunks` rows. Completed chunks are skipped on retry; running/failed chunks can be retried; checkpoints record the last processed employee-day. Worker execution runs the real Timeline -> Matcher -> 24 deterministic rules -> durable finding pipeline.

Finding writes are idempotent by `(scan_id, finding_key)`. Scans capture engine and rule versions. Cancellation is checked between employee-days and propagates to the current chunk.

Behavioral and organizational analytics require the complete scan population and should execute as post-processing/finalization jobs after deterministic chunks finish. They are deliberately not recalculated independently inside every daily chunk because that would produce statistically inconsistent baselines.

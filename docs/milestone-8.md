# Milestone 8 - Distributed Scan Execution

Adds Celery-based background scan execution, Redis broker/backend, date-range chunking, late acknowledgements, worker-loss rejection, bounded retries with backoff, cancellation-aware execution, progress counters, and scan rule/engine version metadata.

Design rule: HTTP creates and controls scans; workers execute them. Large scans never depend on an API request remaining open.

Current worker skeleton processes bounded date chunks and establishes cancellation/checkpoint semantics. The next hardening step should persist one row per chunk so individual chunk retry state survives broker/database failures and workers can resume from the last durable checkpoint.

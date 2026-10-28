# ADR 0008: Background scan execution with bounded idempotent chunks

Status: Accepted

Long-running workforce analysis must not execute synchronously in HTTP requests. Scans are queued to Celery through Redis and divided into bounded date chunks. Tasks use late acknowledgement, retry with exponential backoff and cancellation checks. Analytical output remains idempotent by scan/finding key.

A future production iteration should persist chunk rows and use transactional outbox/event publication if exactly-once orchestration becomes necessary.

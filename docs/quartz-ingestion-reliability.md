# Quartz ingestion reliability

## Scope and safeguards

Quartz access remains read-only. The connector retrieves login sessions and activity versions; Sentinel stores immutable snapshots under one ingestion run. The activity endpoint defaults to batches of 25 session IDs (configurable from 1 to 100). Retry configuration is stored in the connector's existing `config_json`: `request_max_attempts` (default 4), `retry_backoff_base_seconds` (0.5), and `retry_backoff_max_seconds` (20).

Only connection/pool timeouts, read timeouts, connection errors, HTTP 429, and HTTP 502/503/504 are retried. Backoff is exponential with jitter. A valid `Retry-After` value is honored up to the configured maximum delay. Authentication failures, other HTTP errors, malformed payloads, and normalization/validation failures are not retried. Logs include run and batch IDs, page, counts, latency, retry count, and failure category; they omit tokens, cursor values, and employee/session identifiers.

## Durable checkpoint model

Migration `0009_durable_ingestion_progress` adds the checkpoint tables. Migration `0010_ingestion_recovery_audit` adds the explicit legacy recovery actor, timestamp, and attempt count:

- `ingestion_progress`, one row per run, for session pagination, counts, date coverage, reconciliation, last failure, and a worker lease.
- `ingestion_activity_batches`, one deterministic batch per group of source session IDs, for cursor/page state, counts, attempts, failure category, and completion.

Each session page commits the inserted snapshots and its next cursor in one transaction. Each activity page commits inserted snapshots and its next cursor/status in one transaction. A crash before commit leaves both the data and checkpoint unchanged; a crash after commit resumes at the next cursor. Snapshot inserts use the existing unique keys with `ON CONFLICT DO NOTHING`, then verify content hashes so a changed source record within a run fails explicitly. Completed activity batches are skipped on resume. An expiring database lease prevents concurrent workers from processing one run at once.

The lease is not distributed outside PostgreSQL and expires after ten minutes if a worker disappears. A second resume request during a live lease may queue, then receive a safe `already running` failure; it cannot corrupt checkpoint state.

## Completion and reconciliation

Run status describes retrieval lifecycle (`queued`, `running`, `partial`, `failed`, `completed`). Progress status reports analytical evidence readiness:

- `COMPLETE` / `RECONCILED`: all session and activity pages/batches finished and Quartz supplied session and activity expected counts that match unique persisted counts.
- `UNVERIFIED`: retrieval finished, but Quartz did not supply all authoritative expected counts.
- `INCOMPLETE`: retrieval is partial/failed or a count mismatch was detected.

Seven requested calendar dates or successful pagination alone do not establish source completeness. Date coverage reports requested dates and dates with no sessions; a date without sessions may be a valid non-workday or missing source data. Since Quartz currently may not provide expected counts, completed runs can legitimately remain `UNVERIFIED`. No payroll completeness claim should be made from a one-day run.

## Operational endpoints

The existing ingestion router remains manager/admin protected:

- `GET /api/v1/ingestion-runs/{run_id}/progress` returns counts, statuses, batch totals, date coverage, reconciliation, and a safe failure category. It does not return employee IDs, session IDs, cursors, or activity comments.
- The progress endpoint distinguishes `LEGACY_MISSING` from an unknown run (404), reports snapshot counts and lease state, and reports whether recovery is eligible.
- `POST /api/v1/ingestion-runs/{run_id}/recovery-initialize` creates an auditable empty checkpoint for an eligible failed legacy run. It uses a row lock, preserves all snapshots, and is idempotent. It never infers that existing snapshots cover completed pages.
- `POST /api/v1/ingestion-runs/{run_id}/resume` queues only `failed` or `partial` runs. It does not resume `completed` runs.

For a legacy run, initialize first and resume only after an operator reviews the diagnostics. Initialization records the actor, time, and recovery attempt count. Resume also updates recovery attempt metadata. These endpoints are manager/admin protected.

The existing create and run response schemas remain unchanged.

## Configuration example

Set these fields in the Quartz connector `config_json` (or omit them for defaults):

```json
{
  "activity_session_id_batch_size": 25,
  "request_max_attempts": 4,
  "retry_backoff_base_seconds": 0.5,
  "retry_backoff_max_seconds": 20
}
```

Authentication continues through `QUARTZ_API_BEARER_TOKEN`; secrets must not be placed in logs or checked into connector configuration.

## Deployment

Back up the Sentinel database according to the site's normal PostgreSQL procedure, deploy the backend image, then run the additive migration:

```sh
docker compose build api worker
docker compose run --rm api alembic upgrade head
docker compose up -d api worker
```

The repeatable Docker test command is:

```sh
docker compose --profile test run --rm test
```

PostgreSQL integration tests use a disposable database named with `_test` in its name and a temporary schema:

```sh
docker compose up -d postgres
docker compose exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" sentinel_ai_test'
export SENTINEL_TEST_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/sentinel_ai_test"
docker compose --profile test run --rm -e SENTINEL_TEST_DATABASE_URL test pytest -m postgres_integration
```

This creates a separate database alongside the existing database in the current PostgreSQL service; it does not drop or reset existing databases or volumes. Use this only in an explicitly authorized local/test environment. The test fixture creates and drops uniquely named schemas inside `sentinel_ai_test` and refuses a database name without `_test`.

Do not reset volumes. The migration is reversible, but production rollback should first stop workers and assess whether progress rows are still needed. Downgrading removes checkpoint tables but preserves ingestion runs and snapshots; it loses resumability metadata. Prefer application rollback while retaining the additive tables.

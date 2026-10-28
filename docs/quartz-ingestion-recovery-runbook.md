# Quartz ingestion recovery runbook

## Before resuming

1. Apply the additive migration and run the Docker test profile after deployment:

   ```sh
   docker compose run --rm api alembic upgrade head
   docker compose --profile test run --rm test
   ```

2. Inspect the run status and progress using an authenticated manager/admin token:

   ```sh
   curl --fail --silent --show-error \
     -H "Authorization: Bearer $SENTINEL_TOKEN" \
     "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/progress"
   ```

3. Review `checkpoint_availability`, `recovery_eligible`, snapshot totals, lease state, `completion_status`, `reconciliation_status`, failed batch count, source count mismatches, date coverage, and failure category. For a legacy run, `LEGACY_MISSING` means historical page coverage is unknown. `UNVERIFIED` does not establish source or payroll completeness.
4. Confirm the Quartz REST service is healthy and that the stored connector uses the intended date range. Do not query or expose Quartz MySQL directly; do not bypass network/database allowlists.
5. Check that no worker currently holds the run lease. The progress endpoint intentionally omits lease tokens and internal cursors.

## Explicit legacy recovery initialization

If progress returns `checkpoint_availability: LEGACY_MISSING`, initialize only after confirming the run is failed and the operator accepts a full source re-fetch. Initialization is a separate, auditable transaction. It creates checkpoint state with an empty cursor; it does not modify or reconcile existing snapshots.

```sh
curl --fail --silent --show-error -X POST \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/recovery-initialize"
```

Repeated initialization is idempotent. It returns the existing recovery metadata rather than clearing progress or snapshots.

## Controlled resume

After initialization, an operator separately resumes the failed run. Checkpointed modern runs may also be resumed directly. Failed or partial status is required.

```sh
curl --fail --silent --show-error -X POST \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/resume"
```

Poll the progress endpoint. A currently leased run can reject a duplicate worker attempt safely; wait for the active worker or lease expiry and then inspect state again. Do not launch concurrent manual workers against the same run.

## Post-recovery reconciliation

Poll read-only progress until the run is terminal, then inspect the same progress endpoint:

```sh
curl --fail --silent --show-error \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/progress"
```

Confirm session and activity counts, all activity batches completed, no count mismatches, and requested-date coverage. If Quartz did not supply expected source counts, keep the run `UNVERIFIED` even when all retrieved pages completed.

## Historical August 26, 2026 failed run

Run `a62525d0-3d22-4944-a4f3-5cc1540854f7` predates durable checkpoints. Its 17,600 session and 467,697 activity snapshots remain untouched. After migrations 0009 and 0010, the explicit initialization endpoint creates an empty progress row; Sentinel cannot know which activity batches/pages the previous worker completed. The first recovery therefore re-collects the bounded date's session listing and activity batches, with idempotent unique-key/hash checks. It does not delete snapshots. Existing duplicate snapshots are skipped only when content hashes match; changed source content under the same run is surfaced as a conflict for operator review.

Do not retry this historical run automatically. The operator must explicitly initialize recovery, inspect the returned counts and recovery actor, then issue the separate controlled resume request. This remains a single-day ingestion and cannot establish a complete payroll week.

Exact commands after deployment and operator approval:

```sh
export RUN_ID=a62525d0-3d22-4944-a4f3-5cc1540854f7

# Read-only inspect. Confirm LEGACY_MISSING, failed status, existing counts,
# and recovery_eligible=true before continuing.
curl --fail --silent --show-error \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/progress"

# Explicitly initialize; this only creates checkpoint/audit metadata.
curl --fail --silent --show-error -X POST \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/recovery-initialize"

# Inspect the initialized status. Verify original snapshot counts remain 17,600
# and 467,697 (unless an operator reconciles a pre-existing count discrepancy).
curl --fail --silent --show-error \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/progress"

# Separate, deliberate resume. This re-fetches the date from Quartz.
curl --fail --silent --show-error -X POST \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/resume"

# Reconcile after the worker finishes; retain UNVERIFIED if source counts are absent.
curl --fail --silent --show-error \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  "$SENTINEL_API/api/v1/ingestion-runs/$RUN_ID/progress"
```

## Failure handling

- `connection_timeout`, `read_timeout`, `connection_error`, and HTTP 429/502/503/504 are retried a bounded number of times per request.
- `http_401`/`http_403`: stop and repair credentials or access policy; do not increase retries.
- `malformed_response`, validation errors, repeated cursor, or snapshot hash conflict: stop and preserve the run for investigation.
- `INCOMPLETE`: inspect failed batches and run logs, then resume after correcting the cause.
- `MISMATCH`: retain snapshots and escalate count reconciliation to Quartz; do not mark the population complete manually.
- `UNVERIFIED`: retrieve authoritative Quartz counts or record that source completeness could not be established.

Logs contain run/batch UUIDs and aggregate counts, not credentials or employee-level payloads. Restrict access to logs and progress endpoints under existing manager/admin access controls.

## Rollback

Application rollback does not require database reset. Stop the new worker/backend version and deploy the previous image. Keep migration 0009 tables in place unless a reviewed database rollback is explicitly required. The migration downgrade drops only progress/batch checkpoint tables; it leaves ingestion runs and snapshots intact, but destroys resume metadata. Never use `docker compose down -v`.

## Closeout checklist

- Confirm all activity batches are completed.
- Check unique persisted counts and all reported mismatches.
- Confirm whether Quartz supplied expected counts; if absent, retain `UNVERIFIED` readiness.
- Confirm requested/observed date coverage and identify dates with no sessions.
- Record unresolved source count/date evidence gaps.
- Do not interpret successful retrieval as payable-time validation, financial impact, or fraud confirmation.

# Milestone 2: Quartz Connector and Operational Snapshot Ledger

Status: Implemented

## Scope delivered

- Read-only Quartz REST connector.
- Shift-date range extraction with cursor pagination.
- Bounded ingestion: 200 sessions and 1,000 activities per persistence batch.
- Strict normalization of Quartz login sessions and activities.
- Activity source semantics 0 through 5 as a domain enum.
- Immutable ingestion run, session snapshot, and activity snapshot persistence.
- SHA-256 canonical content hashes.
- Idempotency key per connector ingestion request.
- Employee-day read model that retains every login session for the same agent and shift date.
- Connector test endpoint and ingestion APIs.
- Quartz API contract documentation.

## Explicit non-goals

- No fraud rules yet.
- No activity fuzzy matching yet.
- No behavioral scoring yet.
- No AI inference yet.
- No direct Quartz database reads in the primary connector.
- No credential persistence in connector metadata.

## Exit criteria

Milestone 2 is accepted when the repository compiles, connector/normalization tests pass, PostgreSQL migrations apply in CI/local Docker, and a Quartz-compatible API fixture can be ingested into completed immutable snapshots.

## Next milestone

Milestone 3 will build the Timeline Reconstruction Engine over completed snapshots. Its unit of analysis is employee + shift date, with all sessions and all source versions aligned into a canonical timeline.

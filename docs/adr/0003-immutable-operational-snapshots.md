# ADR 0003: Immutable Operational Snapshots

## Status
Accepted

## Context
Quartz remains the operational system of record, but fraud and compliance investigations must be reproducible even if source records are corrected later. Sentinel also needs to avoid analytical queries against Quartz.

## Decision
Every connector ingestion creates an `ingestion_run`. Session and activity records are normalized and written to append-only snapshot tables tied to that run. Each normalized record receives a SHA-256 canonical content hash. Snapshot rows are never updated by the ingestion pipeline.

Failed runs may contain partial snapshots. Their run status is `failed`; downstream analytics must consume only `completed` runs.

## Consequences
- Evidence can be reproduced against the exact data observed during a run.
- Source corrections do not rewrite prior Sentinel evidence.
- Storage consumption is higher than a mutable staging model.
- Retention and archival policies will be required before long-term production rollout.

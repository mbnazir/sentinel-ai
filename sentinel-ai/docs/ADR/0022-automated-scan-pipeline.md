# ADR-0022: Automated scan pipeline from normalized data

## Status

Accepted

## Context

Sentinel has ingestion, timeline reconstruction, matching, rules, and risk scoring, but these components must be orchestrated.

## Decision

Add a scan pipeline that runs from normalized sessions/activities through risk scoring.

## Consequences

- Sentinel can produce risk results from persisted connector data.
- Case creation and scan persistence can be layered next.
- Quartz is no longer queried during analytics execution.

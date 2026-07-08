# ADR-0021: Persist normalized connector output

## Status

Accepted

## Context

Repeated analysis directly from source systems is slow, brittle, and can impact operational systems.

## Decision

Persist connector output into Sentinel-owned normalized stores before analytics.

## Consequences

- Scans become reproducible.
- Analytics do not load Quartz repeatedly.
- Future connectors can normalize into the same schema.

# ADR-0020: Quartz API-first ingestion

## Status

Accepted

## Context

Direct database reads tightly couple Sentinel to Quartz internals and risk performance impact.

## Decision

Use Quartz APIs as the primary ingestion method.

## Consequences

- Sentinel remains decoupled from Quartz schema changes.
- Quartz controls access and throttling.
- Direct DB connector can remain a legacy fallback.

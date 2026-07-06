# ADR-0008: Behavior analytics for pattern detection

## Status

Accepted

## Context

Enterprise investigations are rarely based on one event. Compliance teams need patterns across time, teams, campaigns, and supervisors.

## Decision

Introduce behavior analytics after risk scoring and before investigation case management.

## Consequences

- Sentinel can prioritize repeat patterns over isolated mistakes.
- Later AI summaries will have stronger longitudinal evidence.
- Behavioral features can power executive dashboards.

# ADR-0028: Queue score is separate from risk score

## Status

Accepted

## Context

A high-risk case and an urgent case are related but not identical. Operational queues need SLA and assignment context.

## Decision

Introduce queue score separate from risk score.

## Consequences

- Investigators can prioritize work more effectively.
- SLAs can influence case ordering without corrupting fraud risk.
- Dashboards can show both risk and operational urgency.

# ADR 0004: Chain-aware activity matching

Status: Accepted

## Context
Quartz may retain activity versions from Phone, System, Agent, Supervisor, Manager and Payroll. Comparing every source to every other source creates duplicate evidence and makes investigations noisy.

## Decision
Sentinel reconstructs each agent + shift_date employee-day, preserves all login sessions, and compares activity versions using the workflow chain:

- Phone -> System for observational mismatch evidence.
- System (or Phone fallback) -> Agent.
- Agent (or System/Phone fallback) -> Supervisor.
- Supervisor (or Agent/System/Phone fallback) -> Manager.
- Manager (or Supervisor/Agent/System/Phone fallback) -> Payroll.

Activities are matched using temporal overlap, activity-type agreement and start/end boundary proximity. Unmatched baseline activities are recorded as removed; unmatched comparison activities are recorded as inserted.

## Consequences
- A single manual edit is less likely to produce duplicate findings.
- Missing workflow stages remain analyzable through deterministic fallback.
- Matching emits evidence, not an accusation or fraud decision.
- Later rules may selectively use Phone/System corroboration when stronger evidence is required.

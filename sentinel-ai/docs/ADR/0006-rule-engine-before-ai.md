# ADR-0006: Deterministic rule engine before AI

## Status

Accepted

## Context

AI summaries are useful, but fraud/integrity investigations require defensible evidence. LLM output cannot be the primary detection mechanism.

## Decision

Build deterministic rules first. AI will summarize rule evidence later.

## Consequences

- Findings are explainable and auditable.
- AI becomes an evidence narrator, not an accuser.
- False positives can be reviewed rule-by-rule.

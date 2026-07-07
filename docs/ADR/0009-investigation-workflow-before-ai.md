# ADR-0009: Investigation workflow before AI investigator

## Status

Accepted

## Context

AI summaries are useful only when there is a controlled investigation object to attach them to. Without case management, AI output becomes disconnected from review workflow.

## Decision

Implement investigation case lifecycle before AI investigator.

## Consequences

- AI summaries will attach to real cases.
- Human review remains the control point.
- Evidence, comments, and decisions are auditable.

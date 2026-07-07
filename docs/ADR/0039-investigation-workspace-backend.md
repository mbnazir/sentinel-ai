# ADR-0039: Investigation workspace backend before v1.0 stabilization

## Status

Accepted

## Context

A fraud platform is not complete if investigators cannot work a case in a structured workspace.

## Decision

Add a backend workspace view that composes case data, evidence, notes, and timeline events.

## Consequences

- Frontend can build a real case workspace.
- AI summaries and reports can use the same workspace view.
- v1.0 stabilization has a clear investigator workflow endpoint.

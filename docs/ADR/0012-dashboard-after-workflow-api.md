# ADR-0012: Dashboard after workflow APIs

## Status

Accepted

## Context

A dashboard built before workflow APIs would be fake UI. Milestone 10 created persistence-backed workflow APIs.

## Decision

Build the React dashboard after workflow API scaffolding.

## Consequences

- UI can consume real backend routes.
- Demo fallback remains available for local development.
- Future frontend work can focus on product UX instead of API guessing.

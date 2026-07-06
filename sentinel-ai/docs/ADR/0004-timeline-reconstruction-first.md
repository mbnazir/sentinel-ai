# ADR-0004: Timeline reconstruction before fraud rules

## Status

Accepted

## Context

Session-level duration comparison detects simple cases, but sophisticated manipulation occurs at activity level.

## Decision

Build timeline reconstruction before implementing fraud rules.

## Consequences

- Rules will be evidence-based.
- Activity-level evidence will be available to investigators.
- Matching and scoring can be built on a deterministic foundation.

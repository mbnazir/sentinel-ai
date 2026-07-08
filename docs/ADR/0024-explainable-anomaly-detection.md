# ADR-0024: Explainable anomaly detection before black-box ML

## Status

Accepted

## Context

Fraud detection requires explainability. Black-box model scores are hard to defend in HR/compliance workflows.

## Decision

Start with robust, explainable anomaly scoring using median and MAD.

## Consequences

- Findings remain auditable.
- Investigators can see feature-level reasons.
- A future ML model can be added as a secondary signal.

# ADR-0005: Use confidence-based activity matching

## Status

Accepted

## Context

Activities from different source versions cannot be reliably matched by database ID. Manual edits create new records. Small timing differences are common.

## Decision

Use confidence-based matching based on overlap, time proximity, duration similarity, and activity-type similarity.

## Consequences

- Matching becomes explainable.
- Rules can use classifications instead of raw activity comparison.
- False positives can be tuned through confidence thresholds.

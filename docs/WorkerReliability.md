# Milestone 34 — Worker Reliability

## Purpose

Milestone 33 added a worker runtime. Milestone 34 adds reliability primitives required before production use.

## Added

- retry policy
- exponential backoff decision
- timeout policy
- dead-letter job model
- worker heartbeat repository
- job lease repository
- reliable job runner
- tests

## Current status

This milestone adds reliability components but does not yet replace the worker execution path. The next step is to wire `ReliableJobRunner` into `QueuedJobRunner`.

## Why this matters

Without retries, leases, and DLQ behavior, a production worker can:

- lose failed jobs
- duplicate long-running jobs
- leave investigators blind to failures
- silently skip scheduled scans

## Next milestone

Wire reliability primitives into the real worker runtime and persist dead-letter/heartbeat/lease state.

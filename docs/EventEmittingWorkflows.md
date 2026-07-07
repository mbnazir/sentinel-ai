# Milestone 37 — Event-emitting Workflows

## Purpose

Milestone 36 added the event bus. Milestone 37 starts making workflows emit events.

## Added

- job-to-event mapper
- event-emitting reliable job runner
- investigation event factory
- event-emitting anomaly case attachment wrapper
- workflow subscribers that enqueue follow-up jobs
- tests

## Event flow

```text
quartz_sync job succeeded
    -> quartz_sync_completed
    -> scan_run job enqueued

scan_run job succeeded
    -> scan_completed
    -> behavior_refresh job enqueued

case created/updated
    -> case_created/case_updated
```

## Current limitation

This milestone introduces event-aware services but does not yet replace all existing handlers. The next milestone should wire these wrappers into persistent job registry and worker runtime.

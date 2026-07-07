# Milestone 36 — Domain Event Bus

## Purpose

Sentinel has multiple workflows that should not be tightly coupled. Domain events allow one workflow to complete and trigger downstream reactions without hard-coding service chains.

## Added

- DomainEvent model
- EventType enum
- domain_events table
- event repository
- in-process event bus
- event dispatcher
- default subscribers scaffold
- event listing API
- tests

## Router registry update

Add:

```python
from app.platform.events.api.routes import router as events_router

RouterDefinition(events_router, "/events", ["Events"])
```

## Initial event types

- quartz_sync_completed
- scan_completed
- behavior_profile_refreshed
- anomaly_detected
- case_created
- case_updated
- job_failed

## Next milestone

Wire job handlers and investigation services to emit events.

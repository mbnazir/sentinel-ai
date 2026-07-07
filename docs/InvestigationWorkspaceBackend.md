# Milestone 39 — Investigation Workspace Backend

## Purpose

Sentinel needs an investigator-facing case workspace backend before v1.0 stabilization.

## Added

- workspace timeline event model
- workspace evidence model
- workspace note model
- investigation workspace model
- timeline builder
- workspace service
- workspace API
- tests

## API

```text
GET /api/v1/investigation-workspace/{case_id}
```

## Router registry update

Add:

```python
from app.investigations.workspace.api.routes import router as investigation_workspace_router

RouterDefinition(investigation_workspace_router, "/investigation-workspace", ["Investigation Workspace"])
```

## What this provides

- case summary
- evidence list
- notes
- case-level timeline
- workspace-ready response shape

## Next milestone

Milestone 40 should freeze feature expansion and focus on v1.0 local run, stabilization, docs, migrations, and smoke testing.

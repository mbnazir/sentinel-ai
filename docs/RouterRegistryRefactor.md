# Milestone 29 — Router Registry + Platform Refactor

## Purpose

Manual edits to `backend/app/api/v1/router.py` became a merge-conflict hotspot. Milestone 29 introduces a router registry so future features register in one central registry.

## Added

- RouterDefinition
- ROUTER_REGISTRY
- register_routers()
- duplicate-prefix validation
- platform route listing endpoint
- tests

## Required manual replacement

Replace `backend/app/api/v1/router.py` with:

```python
from fastapi import APIRouter

from app.platform.routing.register_routers import register_routers
from app.platform.routing.router_registry import ROUTER_REGISTRY

api_v1_router = register_routers(APIRouter(), ROUTER_REGISTRY)
```

## Rule going forward

Future milestones should add routers to `ROUTER_REGISTRY`, not directly to `backend/app/api/v1/router.py`.

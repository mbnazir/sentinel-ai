from fastapi import APIRouter, Depends
from app.core.auth import Role, require_roles

from app.api.v1.routes_assessments import router as assessments_router
from app.api.v1.routes_ai import router as ai_router
from app.api.v1.routes_connectors import router as connectors_router
from app.api.v1.routes_dashboard import router as dashboard_router
from app.api.v1.routes_employee_days import router as employee_days_router
from app.api.v1.routes_weekly import router as weekly_router
from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_ingestion import router as ingestion_router
from app.api.v1.routes_investigations import router as investigations_router
from app.api.v1.routes_organization import router as organization_router
from app.api.v1.routes_timelines import router as timelines_router

api_router = APIRouter()
api_router.include_router(assessments_router, dependencies=[Depends(require_roles(Role.VIEWER, Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])
api_router.include_router(health_router)
api_router.include_router(connectors_router, dependencies=[Depends(require_roles(Role.ADMIN))])
api_router.include_router(ingestion_router, dependencies=[Depends(require_roles(Role.MANAGER, Role.ADMIN))])
api_router.include_router(employee_days_router, dependencies=[Depends(require_roles(Role.VIEWER, Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])
api_router.include_router(weekly_router, dependencies=[Depends(require_roles(Role.VIEWER, Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])
api_router.include_router(timelines_router, dependencies=[Depends(require_roles(Role.VIEWER, Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])

api_router.include_router(organization_router, dependencies=[Depends(require_roles(Role.VIEWER, Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])

api_router.include_router(investigations_router, dependencies=[Depends(require_roles(Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])

api_router.include_router(dashboard_router, dependencies=[Depends(require_roles(Role.VIEWER, Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])

api_router.include_router(ai_router, dependencies=[Depends(require_roles(Role.INVESTIGATOR, Role.MANAGER, Role.ADMIN))])

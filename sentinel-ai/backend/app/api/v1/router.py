from fastapi import APIRouter
from app.security.api.routes import router as security_router
from app.dashboard.api.routes import router as executive_dashboard_router
from app.workflows.api.routes import router as workflow_router
from app.ai.api.routes import router as ai_router
from app.investigations.api.routes import router as investigation_cases_router
from app.analytics.behavior.api.routes import router as behavior_router
from app.scoring.api.routes import router as scoring_router
from app.rules.api.routes import router as rules_router
from app.matcher.api.routes import router as match_router
from app.timeline.api.routes import router as timeline_router

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.connectors.routes import router as connectors_router
from app.api.v1.health.routes import router as health_router
from app.api.v1.scans.routes import router as scans_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, prefix="/health", tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(scans_router, prefix="/scans", tags=["Scans"])
api_v1_router.include_router(connectors_router, prefix="/connectors", tags=["Connectors"])

api_v1_router.include_router(timeline_router, prefix="/timelines", tags=["Timelines"])

api_v1_router.include_router(match_router, prefix="/matches", tags=["Activity Matching"])

api_v1_router.include_router(rules_router, prefix="/rules", tags=["Rules"])

api_v1_router.include_router(scoring_router, prefix="/risk", tags=["Risk Scoring"])

api_v1_router.include_router(behavior_router, prefix="/behavior", tags=["Behavior Analytics"])

api_v1_router.include_router(investigation_cases_router, prefix="/investigations", tags=["Investigations"])

api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI Investigator"])

api_v1_router.include_router(workflow_router, prefix="/workflow", tags=["Workflow"])

api_v1_router.include_router(executive_dashboard_router, prefix="/dashboard", tags=["Executive Dashboard"])

api_v1_router.include_router(security_router, prefix="/security", tags=["Security"])

from fastapi import APIRouter
from app.scoring.api.routes import router as scoring_router
from app.rules.api.routes import router as rules_router
from app.matcher.api.routes import router as match_router
from app.timeline.api.routes import router as timeline_router

from app.api.v1.auth.routes import router as auth_router
from app.api.v1.connectors.routes import router as connectors_router
from app.api.v1.health.routes import router as health_router
from app.api.v1.scans.routes import router as scans_router
from app.anomaly.api.persistence_routes import router as anomaly_persistence_router
from app.anomaly.api.case_routes import router as anomaly_case_router

api_v1_router.include_router(
    anomaly_case_router,
    prefix="/anomaly-cases",
    tags=["Anomaly Cases"],
)

api_v1_router.include_router(
    anomaly_persistence_router,
    prefix="/anomaly-persistence",
    tags=["Anomaly Persistence"],
)

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, prefix="/health", tags=["Health"])
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(scans_router, prefix="/scans", tags=["Scans"])
api_v1_router.include_router(connectors_router, prefix="/connectors", tags=["Connectors"])

api_v1_router.include_router(timeline_router, prefix="/timelines", tags=["Timelines"])

api_v1_router.include_router(match_router, prefix="/matches", tags=["Activity Matching"])

api_v1_router.include_router(rules_router, prefix="/rules", tags=["Rules"])

api_v1_router.include_router(scoring_router, prefix="/risk", tags=["Risk Scoring"])

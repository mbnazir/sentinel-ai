from app.analytics.behavior.api.persistent_routes import router as persistent_behavior_router
from app.anomaly.api.case_routes import router as anomaly_case_router
from app.anomaly.api.persistence_routes import router as anomaly_persistence_router
from app.anomaly.api.routes import router as anomaly_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.connectors.routes import router as connectors_router
from app.api.v1.health.routes import router as health_router
from app.api.v1.scans.routes import router as scans_router
from app.investigations.queue.api_routes import router as investigation_queue_router
from app.matcher.api.routes import router as match_router
from app.platform.routing.router_definition import RouterDefinition
from app.rules.api.routes import router as rules_router
from app.scoring.api.routes import router as scoring_router
from app.timeline.api.routes import router as timeline_router


ROUTER_REGISTRY: list[RouterDefinition] = [
    RouterDefinition(health_router, "/health", ["Health"]),
    RouterDefinition(auth_router, "/auth", ["Authentication"]),
    RouterDefinition(scans_router, "/scans", ["Scans"]),
    RouterDefinition(connectors_router, "/connectors", ["Connectors"]),
    RouterDefinition(timeline_router, "/timelines", ["Timelines"]),
    RouterDefinition(match_router, "/matches", ["Activity Matching"]),
    RouterDefinition(rules_router, "/rules", ["Rules"]),
    RouterDefinition(scoring_router, "/risk", ["Risk Scoring"]),
    RouterDefinition(persistent_behavior_router, "/behavior-intelligence", ["Behavior Intelligence"]),
    RouterDefinition(anomaly_router, "/anomaly", ["Anomaly Detection"]),
    RouterDefinition(anomaly_persistence_router, "/anomaly-persistence", ["Anomaly Persistence"]),
    RouterDefinition(anomaly_case_router, "/anomaly-cases", ["Anomaly Cases"]),
    RouterDefinition(investigation_queue_router, "/investigation-queue", ["Investigation Queue"]),
]

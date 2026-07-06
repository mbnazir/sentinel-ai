from pydantic import BaseModel


class FeatureMetricRequest(BaseModel):
    name: str
    value: float


class FeatureVectorRequest(BaseModel):
    entity_type: str
    entity_id: str
    metrics: list[FeatureMetricRequest]


class AnomalyScoreRequest(BaseModel):
    target: FeatureVectorRequest
    peers: list[FeatureVectorRequest]


class FeatureAnomalyResponse(BaseModel):
    feature_name: str
    value: float
    baseline: float
    deviation: float
    contribution: float
    reason: str


class AnomalyScoreResponse(BaseModel):
    entity_type: str
    entity_id: str
    score: int
    severity: str
    anomalies: list[FeatureAnomalyResponse]
    summary: str

from datetime import datetime, timezone
from uuid import uuid4

from app.matcher.services.source_match_service import SourceMatchService
from app.rules.domain.rule_context import RuleContext
from app.rules.engine.default_rules import build_default_rules
from app.rules.engine.rule_engine import RuleEngine
from app.scans.domain.scan_models import ScanRequest, ScanStatus, ScanSummary, SessionScanResult
from app.scans.services.normalized_activity_mapper import NormalizedActivityMapper
from app.scans.services.normalized_scan_repository import NormalizedScanRepository
from app.scoring.services.risk_scorer import RiskScorer
from app.timeline.domain.source import DataSource
from app.timeline.services.timeline_builder import TimelineBuilder


class ScanPipelineService:
    """Runs end-to-end scanning from normalized data.

    Flow:
    normalized sessions -> activities -> timeline -> matching -> rules -> risk score.
    Investigation case creation is intentionally left as integration boundary because
    repositories differ by deployment mode.
    """

    def __init__(
        self,
        repository: NormalizedScanRepository,
        timeline_builder: TimelineBuilder | None = None,
        source_matcher: SourceMatchService | None = None,
        rule_engine: RuleEngine | None = None,
        risk_scorer: RiskScorer | None = None,
        mapper: NormalizedActivityMapper | None = None,
    ) -> None:
        self.repository = repository
        self.timeline_builder = timeline_builder or TimelineBuilder()
        self.source_matcher = source_matcher or SourceMatchService()
        self.rule_engine = rule_engine or RuleEngine(build_default_rules())
        self.risk_scorer = risk_scorer or RiskScorer()
        self.mapper = mapper or NormalizedActivityMapper()

    def run(self, request: ScanRequest) -> ScanSummary:
        started_at = datetime.now(timezone.utc)
        scan_id = f"SCAN-{uuid4().hex[:12].upper()}"
        results: list[SessionScanResult] = []

        sessions = self.repository.list_sessions_for_shift_range(
            organization_id=request.organization_id,
            shift_date_from=request.shift_date_from,
            shift_date_to=request.shift_date_to,
        )

        for session in sessions:
            activities = self.repository.list_activities_for_session(
                organization_id=request.organization_id,
                login_session_external_id=session.external_id,
            )
            snapshots = [self.mapper.to_snapshot(activity) for activity in activities]
            timeline = self.timeline_builder.build(session.external_id, snapshots)

            matches_by_pair = {}
            for comparison_source in [
                DataSource.AGENT,
                DataSource.SUPERVISOR,
                DataSource.MANAGER,
                DataSource.PAYROLL,
            ]:
                matches_by_pair[(DataSource.SYSTEM, comparison_source)] = (
                    self.source_matcher.match_timeline_sources(
                        timeline,
                        DataSource.SYSTEM,
                        comparison_source,
                    )
                )

            context = RuleContext(
                login_session_external_id=session.external_id,
                timeline=timeline,
                matches_by_source_pair=matches_by_pair,
            )
            rule_results = self.rule_engine.evaluate(context)
            risk = self.risk_scorer.score_session(session.external_id, rule_results)

            results.append(
                SessionScanResult(
                    login_session_external_id=session.external_id,
                    risk_score=risk.risk_score,
                    risk_level=risk.risk_level.value,
                    rule_count=len(rule_results),
                    case_created=False,
                    case_id=None,
                )
            )

        return ScanSummary(
            scan_id=scan_id,
            organization_id=request.organization_id,
            status=ScanStatus.COMPLETED,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            sessions_scanned=len(sessions),
            cases_created=sum(1 for result in results if result.case_created),
            results=results,
        )

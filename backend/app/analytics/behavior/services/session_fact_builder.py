from app.analytics.behavior.domain.session_fact import SessionRiskFact
from app.scans.domain.scan_models import SessionScanResult


class SessionFactBuilder:
    """Builds behavior facts from scan results.

    This is intentionally separated because future versions will enrich facts from
    rule result persistence, campaign/site mappings, payroll users, and supervisor decisions.
    """

    def from_scan_result(
        self,
        result: SessionScanResult,
        agent_external_id: str | None,
        supervisor_external_id: str | None,
        shift_date,
    ) -> SessionRiskFact:
        return SessionRiskFact(
            login_session_external_id=result.login_session_external_id,
            agent_external_id=agent_external_id,
            supervisor_external_id=supervisor_external_id,
            manager_external_id=None,
            campaign_external_id=None,
            site_external_id=None,
            shift_date=shift_date,
            risk_score=result.risk_score,
            rule_count=result.rule_count,
        )

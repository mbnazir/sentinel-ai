from datetime import date

from app.analytics.organization_engine import assess_organization
from app.analytics.organization_models import OrganizationalDailyBehavior


def row(
    agent: str,
    day: int,
    *,
    supervisor: str = "S1",
    manager: str | None = None,
    campaign: str = "C1",
    site: str | None = "SITE1",
    gain: int = 0,
    risk: float = 10,
    supervisor_additions: int = 0,
    manager_additions: int = 0,
    payroll_adjustments: int = 0,
) -> OrganizationalDailyBehavior:
    return OrganizationalDailyBehavior(
        agent_id=agent,
        shift_date=date(2026, 8, day),
        supervisor_id=supervisor,
        manager_id=manager,
        campaign_id=campaign,
        site_id=site,
        risk_score=risk,
        manual_gain_seconds=gain,
        supervisor_additions=supervisor_additions,
        manager_additions=manager_additions,
        payroll_adjustments=payroll_adjustments,
    )


def test_repeated_supervisor_agent_pair_is_flagged() -> None:
    rows = [row("A1", d, supervisor_additions=1) for d in range(1, 5)]
    result = assess_organization(rows, date(2026, 8, 1), date(2026, 8, 4))
    codes = {item.code for item in result.relationship_findings}
    assert "OI-R001" in codes
    assert "OI-S001" in codes


def test_manager_relationship_runs_only_when_hierarchy_exists() -> None:
    rows = [row("A1", d, manager="M1", manager_additions=1) for d in range(1, 5)]
    result = assess_organization(rows, date(2026, 8, 1), date(2026, 8, 4))
    codes = {item.code for item in result.relationship_findings}
    assert "OI-R002" in codes
    assert "OI-M001" in codes
    assert not any("Manager hierarchy is unavailable" in note for note in result.data_quality_notes)


def test_missing_manager_hierarchy_is_reported_not_inferred() -> None:
    rows = [row("A1", 1), row("A2", 2)]
    result = assess_organization(rows, date(2026, 8, 1), date(2026, 8, 2))
    assert any("Manager hierarchy is unavailable" in note for note in result.data_quality_notes)
    assert not result.manager_profiles


def test_payroll_concentration_is_team_signal_not_actor_attribution() -> None:
    rows = [row(f"A{i}", i, supervisor="S1", payroll_adjustments=1) for i in range(1, 6)]
    rows += [row("B1", 6, supervisor="S2")]
    result = assess_organization(rows, date(2026, 8, 1), date(2026, 8, 6))
    finding = next(item for item in result.relationship_findings if item.code == "OI-P001")
    assert finding.relationship_type == "payroll_supervisor_team"
    assert "Payroll actor identity is unavailable" in finding.reason


def test_campaign_peer_outlier_requires_population_and_days() -> None:
    rows = []
    for d in range(1, 7):
        rows.append(row(f"A{d}", d, campaign="C1", gain=20000))
        rows.append(row(f"B{d}", d, campaign="C2", gain=100))
        rows.append(row(f"C{d}", d, campaign="C3", gain=100))
        rows.append(row(f"D{d}", d, campaign="C4", gain=100))
        rows.append(row(f"E{d}", d, campaign="C5", gain=100))
    result = assess_organization(rows, date(2026, 8, 1), date(2026, 8, 6))
    assert "OI-C001" in {item.code for item in result.relationship_findings}


def test_repeated_manager_supervisor_agent_chain_is_flagged() -> None:
    rows = [
        row("A1", d, supervisor="S1", manager="M1", supervisor_additions=1, manager_additions=1)
        for d in range(1, 4)
    ]
    result = assess_organization(rows, date(2026, 8, 1), date(2026, 8, 3))
    finding = next(item for item in result.relationship_findings if item.code == "OI-R003")
    assert finding.subject_ids == ("M1", "S1", "A1")
    assert "relationship-risk signal" in finding.reason

import pytest
from app.finalization.models import ScanSummary

def test_scan_summary_total():
    s=ScanSummary(employee_days=10,deterministic_findings=5,behavioral_findings=2,organizational_findings=1,total_findings=8,high_or_critical=3,max_risk_score=30)
    assert s.total_findings==8

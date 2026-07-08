from app.ai.services.narrative_parser import NarrativeParser


def test_narrative_parser_extracts_sections() -> None:
    raw = """Executive Summary:
Needs review.

Key Findings:
- Finding one
- Finding two

Evidence Summary:
- Evidence one

Recommended Next Steps:
- Step one

Limitations:
- Limited to provided evidence
"""

    narrative = NarrativeParser().parse("CASE-1", raw)

    assert narrative.executive_summary == "Needs review."
    assert narrative.key_findings == ["Finding one", "Finding two"]
    assert narrative.evidence_summary == ["Evidence one"]
    assert narrative.recommended_next_steps == ["Step one"]
    assert narrative.limitations == ["Limited to provided evidence"]

from app.investigations.domain.case import InvestigationCase


class InvestigationPromptBuilder:
    """Builds deterministic, evidence-grounded prompts for investigation summaries."""

    SYSTEM_PROMPT = """You are Sentinel AI, an enterprise workforce integrity assistant.

Rules:
- Do not accuse anyone of fraud.
- Do not make legal or HR conclusions.
- Summarize only the evidence provided.
- Clearly separate findings, evidence, recommended next steps, and limitations.
- Use neutral language such as "requires review", "risk indicator", and "potential anomaly".
"""

    def build_case_prompt(self, case: InvestigationCase) -> str:
        evidence_lines = [
            f"- [{link.evidence_type}] {link.source}: {link.summary}"
            for link in case.evidence_links
        ]
        comments = [f"- {comment.author_id}: {comment.body}" for comment in case.comments]

        return f"""
Case ID: {case.case_id}
Entity Type: {case.entity_type}
Entity ID: {case.entity_id}
Risk Score: {case.risk_score}
Priority: {case.priority.value}
Status: {case.status.value}
Summary: {case.summary}

Evidence:
{chr(10).join(evidence_lines) if evidence_lines else "- No evidence links provided."}

Investigation Comments:
{chr(10).join(comments) if comments else "- No comments provided."}

Produce:
1. Executive Summary
2. Key Findings
3. Evidence Summary
4. Recommended Next Steps
5. Limitations
""".strip()

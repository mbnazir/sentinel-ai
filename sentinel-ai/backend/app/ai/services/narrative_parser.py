from app.ai.domain.investigation_narrative import InvestigationNarrative


class NarrativeParser:
    """Converts model output into a structured narrative.

    Milestone 9 uses conservative parsing. Later versions can request strict JSON output.
    """

    def parse(self, case_id: str, raw_output: str) -> InvestigationNarrative:
        return InvestigationNarrative(
            case_id=case_id,
            executive_summary=self._section(raw_output, "Executive Summary"),
            key_findings=self._bullets(self._section(raw_output, "Key Findings")),
            evidence_summary=self._bullets(self._section(raw_output, "Evidence Summary")),
            recommended_next_steps=self._bullets(self._section(raw_output, "Recommended Next Steps")),
            limitations=self._bullets(self._section(raw_output, "Limitations")),
            raw_model_output=raw_output,
        )

    def _section(self, text: str, heading: str) -> str:
        marker = f"{heading}:"
        if marker not in text:
            return ""

        start = text.index(marker) + len(marker)
        possible_headings = [
            "Executive Summary:",
            "Key Findings:",
            "Evidence Summary:",
            "Recommended Next Steps:",
            "Limitations:",
        ]

        end = len(text)
        for next_heading in possible_headings:
            if next_heading == marker:
                continue
            position = text.find(next_heading, start)
            if position != -1:
                end = min(end, position)

        return text[start:end].strip()

    def _bullets(self, section: str) -> list[str]:
        if not section:
            return []
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        cleaned = [line[2:].strip() if line.startswith("- ") else line for line in lines]
        return cleaned

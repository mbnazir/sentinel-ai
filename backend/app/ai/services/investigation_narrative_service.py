from app.ai.domain.ai_request import AIMessage, AIRequest
from app.ai.domain.investigation_narrative import InvestigationNarrative
from app.ai.providers.base_provider import BaseAIProvider
from app.ai.providers.mock_provider import MockAIProvider
from app.ai.services.narrative_parser import NarrativeParser
from app.ai.services.prompt_builder import InvestigationPromptBuilder
from app.investigations.domain.case import InvestigationCase


class InvestigationNarrativeService:
    def __init__(
        self,
        provider: BaseAIProvider | None = None,
        prompt_builder: InvestigationPromptBuilder | None = None,
        parser: NarrativeParser | None = None,
    ) -> None:
        self.provider = provider or MockAIProvider()
        self.prompt_builder = prompt_builder or InvestigationPromptBuilder()
        self.parser = parser or NarrativeParser()

    async def generate_for_case(self, case: InvestigationCase) -> InvestigationNarrative:
        prompt = self.prompt_builder.build_case_prompt(case)
        request = AIRequest(
            messages=[
                AIMessage(role="system", content=InvestigationPromptBuilder.SYSTEM_PROMPT),
                AIMessage(role="user", content=prompt),
            ],
            temperature=0.1,
            max_tokens=1200,
            metadata={"case_id": case.case_id},
        )
        response = await self.provider.generate(request)
        return self.parser.parse(case.case_id, response.content)

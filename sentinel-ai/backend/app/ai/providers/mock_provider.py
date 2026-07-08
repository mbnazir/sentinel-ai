from app.ai.domain.ai_request import AIRequest
from app.ai.domain.ai_response import AIResponse
from app.ai.providers.base_provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    provider_name = "mock"
    model_name = "mock-investigator-v1"

    async def generate(self, request: AIRequest) -> AIResponse:
        user_content = request.messages[-1].content if request.messages else ""
        return AIResponse(
            content=(
                "Executive Summary:\n"
                "This case contains integrity risk indicators requiring human review.\n\n"
                "Key Findings:\n"
                "- Evidence shows one or more rule-based findings.\n"
                "- The risk score should be treated as investigation priority, not proof of fraud.\n\n"
                "Evidence Summary:\n"
                f"- Input evidence length: {len(user_content)} characters.\n\n"
                "Recommended Next Steps:\n"
                "- Review source activities and supervisor/payroll actions.\n"
                "- Validate against operational context and approved exceptions.\n\n"
                "Limitations:\n"
                "- This narrative is generated from provided rule evidence only."
            ),
            provider=self.provider_name,
            model=self.model_name,
            input_tokens=None,
            output_tokens=None,
        )

from app.ai.domain.ai_request import AIRequest
from app.ai.domain.ai_response import AIResponse
from app.ai.providers.base_provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider scaffold.

    Real API wiring is intentionally not enabled in Milestone 9 to avoid hardcoding secrets
    or vendor lock-in. The provider interface is ready for later implementation.
    """

    provider_name = "openai"
    model_name = "configured-model"

    async def generate(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError("OpenAI provider wiring will be implemented with secure config.")

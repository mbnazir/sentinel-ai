from abc import ABC, abstractmethod

from app.ai.domain.ai_request import AIRequest
from app.ai.domain.ai_response import AIResponse


class BaseAIProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError

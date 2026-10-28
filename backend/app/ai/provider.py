from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def summarize(self,prompt:str)->str: ...

class DisabledProvider(AIProvider):
    async def summarize(self,prompt:str)->str:
        raise RuntimeError("AI provider is disabled")

import httpx
from app.ai.provider import AIProvider

class OpenAICompatibleProvider(AIProvider):
    def __init__(self,*,base_url:str,api_key:str,model:str):
        self.base_url=base_url.rstrip("/")
        self.api_key=api_key
        self.model=model
    async def summarize(self,prompt:str)->str:
        async with httpx.AsyncClient(timeout=60) as client:
            r=await client.post(f"{self.base_url}/chat/completions",headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},json={
                "model":self.model,
                "temperature":0,
                "messages":[
                    {"role":"system","content":"You are Sentinel AI Investigator. Summarize only supplied evidence. Never declare fraud or guilt. Distinguish observed facts, risk signals, data-quality limitations, and recommended review steps."},
                    {"role":"user","content":prompt},
                ],
            })
            r.raise_for_status()
            return str(r.json()["choices"][0]["message"]["content"])

class GeminiProvider(AIProvider):
    def __init__(self,*,api_key:str,model:str):
        self.api_key=api_key; self.model=model
    async def summarize(self,prompt:str)->str:
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        body={"generationConfig":{"temperature":0},"contents":[{"role":"user","parts":[{"text":"You are Sentinel AI Investigator. Summarize only supplied evidence. Never declare fraud or guilt. Distinguish facts, risk signals, data-quality limitations, and recommended review steps.\n\n"+prompt}]}]}
        async with httpx.AsyncClient(timeout=60) as client:
            r=await client.post(url,json=body); r.raise_for_status()
            return str(r.json()["candidates"][0]["content"]["parts"][0]["text"])

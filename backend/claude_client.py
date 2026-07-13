import os

from groq import AsyncGroq

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class ClaudeClient:
    def __init__(self, api_key: str | None = None):
        self.client = AsyncGroq(api_key=api_key)

    async def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 2048,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

import os

from anthropic import AsyncAnthropic

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")


class ClaudeClient:
    def __init__(self, api_key: str | None = None):
        self.client = AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 2048,
    ) -> str:
        response = await self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[
                {"role": "user", "content": user},
            ],
        )
        return response.content[0].text
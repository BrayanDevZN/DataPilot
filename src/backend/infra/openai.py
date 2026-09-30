"""Async OpenAI Responses API client used by the infrastructure layer."""

from typing import Any

from openai import AsyncOpenAI

from src.backend.logs.log import log_operation


class OpenAIClient:
    @log_operation
    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = AsyncOpenAI(api_key=api_key)

    @log_operation
    async def send(
        self,
        prompt: str | list[dict[str, Any]],
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 1.0,
        previous_response_id: str | None = None,
    ):
        return await self.client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            previous_response_id=previous_response_id,
        )

    @log_operation
    async def send_with_tools(
        self,
        prompt: str | list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 1.0,
        tool_choice: str | dict[str, Any] = "auto",
        previous_response_id: str | None = None,
    ):
        return await self.client.responses.create(
            model=model,
            input=prompt,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            previous_response_id=previous_response_id,
        )

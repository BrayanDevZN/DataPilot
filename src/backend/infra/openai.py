"""OpenAI Responses API client used by the infrastructure layer."""

from typing import Any

from openai import OpenAI

from src.backend.logs.log import log_operation


class OpenAIClient:
    @log_operation
    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=api_key)

    @log_operation
    def send(
        self,
        prompt: str | list[dict[str, Any]],
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 1.0,
    ):
        return self.client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
        )

    @log_operation
    def send_with_tools(
        self,
        prompt: str | list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 1.0,
        tool_choice: str | dict[str, Any] = "auto",
    ):
        return self.client.responses.create(
            model=model,
            input=prompt,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
        )

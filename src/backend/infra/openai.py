"""Async OpenAI Responses API client with a deterministic test mode."""

import json
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from openai import AsyncOpenAI

from src.backend.logs.log import log_operation


@dataclass
class TestOpenAIResponse:
    output_text: str
    output: list[Any]
    id: str


class OpenAIClient:
    @log_operation
    def __init__(
        self,
        api_key: str | None,
        *,
        environment: str = "prod",
    ) -> None:
        self.environment = environment
        self.api_key = api_key
        self.client: AsyncOpenAI | None = None

        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        elif environment != "test":
            raise ValueError("OPENAI_API_KEY is required outside test mode")

    def _test_response(
        self,
        prompt: str | list[dict[str, Any]],
    ) -> TestOpenAIResponse:
        prompt_text = (
            prompt
            if isinstance(prompt, str)
            else json.dumps(prompt, ensure_ascii=False, default=str)
        )

        if (
            "Dashboard Planner Agent" in prompt_text
            or '"tool": "dashboard_plan"' in prompt_text
        ):
            output_text = json.dumps(
                {
                    "tool": "dashboard_plan",
                    "dataset_type": "generico",
                    "analysis_type": "general",
                    "business_context": "Resposta de teste sem chamada externa.",
                    "priority_metrics": [],
                    "rename_columns": {},
                    "charts": [
                        {
                            "title": "Tabela de teste",
                            "operation": "table",
                            "chart_type": "table",
                            "group_by": [],
                            "metric": [],
                            "aggregation": ["none"],
                            "x": None,
                            "y": None,
                            "time_column": None,
                            "time_freq": "M",
                            "drill_down_hierarchy": [],
                            "filters": [],
                            "limit": 20,
                            "sort": "none",
                            "reason": "Chart gerado em modo de teste.",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        else:
            output_text = (
                "Resposta de teste do DataPilot. "
                "Nenhuma requisição foi enviada para a OpenAI."
            )

        return TestOpenAIResponse(
            output_text=output_text,
            output=[],
            id=f"test_{uuid4()}",
        )

    @log_operation
    async def send(
        self,
        prompt: str | list[dict[str, Any]],
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 1.0,
        previous_response_id: str | None = None,
    ):
        if self.client is None:
            return self._test_response(prompt)

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
        if self.client is None:
            return self._test_response(prompt)

        return await self.client.responses.create(
            model=model,
            input=prompt,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            previous_response_id=previous_response_id,
        )

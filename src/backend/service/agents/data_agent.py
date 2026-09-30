"""Data analysis agent that executes deterministic dataframe tools."""

import asyncio
import json
from typing import Any

from src.backend.infra.manage import openai, prompts

from .tool import ANALYTICS_TOOL, AgentDataTools


class DataAgent:
    def __init__(
        self,
        data,
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
        spark_threshold: int = 100_000,
        max_tool_rounds: int = 8,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tool_rounds = max_tool_rounds
        self.tools = AgentDataTools(
            data,
            spark_threshold=spark_threshold,
        )

    def _build_prompt(
        self,
        question: str,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        history = history or []
        if hasattr(self.tools.data, "collect_schema"):
            columns = self.tools.data.collect_schema().names()
        else:
            columns = list(self.tools.data.columns)

        unique_values = self.tools.tool.unique_values(
            self.tools.data,
            columns=columns,
            limit=12,
        )

        return (
            prompts.interpreter_analysis
            .replace("{{QUESTION}}", question)
            .replace("{{COLUMNS}}", json.dumps(columns, ensure_ascii=False))
            .replace("{{UNIQUE_VALUES}}", json.dumps(unique_values, ensure_ascii=False, default=str))
            .replace("{{HISTORY}}", json.dumps(history, ensure_ascii=False, default=str))
        )

    async def run(
        self,
        question: str,
        *,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        prompt = self._build_prompt(question, history)

        response = await openai.send_with_tools(
            prompt,
            tools=[ANALYTICS_TOOL],
            model=self.model,
            temperature=self.temperature,
        )

        for _ in range(self.max_tool_rounds):
            calls = [
                item
                for item in response.output
                if getattr(item, "type", None) == "function_call"
                and getattr(item, "name", None) == ANALYTICS_TOOL["name"]
            ]

            if not calls:
                return response.output_text

            tool_outputs = []

            for call in calls:
                arguments = json.loads(call.arguments or "{}")
                result = await asyncio.to_thread(
                    self.tools.execute,
                    arguments,
                )

                tool_outputs.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str,
                    ),
                })

            response = await openai.send_with_tools(
                tool_outputs,
                tools=[ANALYTICS_TOOL],
                model=self.model,
                temperature=self.temperature,
                previous_response_id=response.id,
            )

        raise RuntimeError("Agent exceeded the maximum number of tool rounds")

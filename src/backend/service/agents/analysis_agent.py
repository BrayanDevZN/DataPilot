"""Single-result analysis agent."""

import json
from typing import Any

from src.backend.infra.manage import openai, prompts


class AnalysisAgent:
    def __init__(
        self,
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.4,
    ) -> None:
        self.model = model
        self.temperature = temperature

    async def run(
        self,
        *,
        question: str | None,
        chart: dict[str, Any] | None,
        interpretation: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        prompt = (
            prompts.generator_analysis
            .replace("{{QUESTION}}", question or "")
            .replace("{{CHART}}", json.dumps(chart, ensure_ascii=False, default=str))
            .replace("{{INTERPRETATION}}", json.dumps(interpretation, ensure_ascii=False, default=str))
            .replace("{{HISTORY}}", json.dumps(history or [], ensure_ascii=False, default=str))
        )
        response = await openai.send(
            prompt,
            model=self.model,
            temperature=self.temperature,
        )
        return response.output_text

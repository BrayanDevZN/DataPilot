"""Multi-result analysis agent."""

import json
from typing import Any

from src.backend.infra.manage import openai, prompts


class MultiAnalysisAgent:
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
        charts: list[dict[str, Any]],
        interpretation: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        prompt = (
            prompts.generator_analysis_multi
            .replace("{{QUESTION}}", question or "")
            .replace("{{CHARTS}}", json.dumps(charts, ensure_ascii=False, default=str))
            .replace("{{INTERPRETATION}}", json.dumps(interpretation, ensure_ascii=False, default=str))
            .replace("{{HISTORY}}", json.dumps(history or [], ensure_ascii=False, default=str))
        )
        response = await openai.send(
            prompt,
            model=self.model,
            temperature=self.temperature,
        )
        return response.output_text

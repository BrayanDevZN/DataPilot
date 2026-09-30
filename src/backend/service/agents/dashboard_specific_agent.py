"""Specific dashboard narrative agent."""

import json
from typing import Any

from src.backend.infra.manage import openai, prompts


class DashboardSpecificAgent:
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
        user_prompt: str,
        plan: dict[str, Any],
        schema: dict[str, Any],
        metrics: list[dict[str, Any]],
    ) -> str:
        prompt = (
            prompts.generator_dashboard_specific
            .replace("{{USER_PROMPT}}", user_prompt)
            .replace("{{PLAN}}", json.dumps(plan, ensure_ascii=False, default=str))
            .replace("{{SCHEMA}}", json.dumps(schema, ensure_ascii=False, default=str))
            .replace("{{METRICS}}", json.dumps(metrics, ensure_ascii=False, default=str))
        )
        response = await openai.send(
            prompt,
            model=self.model,
            temperature=self.temperature,
        )
        return response.output_text

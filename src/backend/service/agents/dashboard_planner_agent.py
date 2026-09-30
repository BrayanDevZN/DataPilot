"""Dashboard planning agent."""

import json
from typing import Any

from src.backend.infra.manage import openai, prompts


class DashboardPlannerAgent:
    def __init__(
        self,
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
    ) -> None:
        self.model = model
        self.temperature = temperature

    async def run(self, user_prompt: str | None, schema: dict[str, Any]) -> str:
        prompt = (
            prompts.interpreter_dashboard_plan
            .replace("{{USER_PROMPT}}", user_prompt or "")
            .replace("{{SCHEMA}}", json.dumps(schema, ensure_ascii=False, default=str))
        )
        response = await openai.send(
            prompt,
            model=self.model,
            temperature=self.temperature,
        )
        return response.output_text

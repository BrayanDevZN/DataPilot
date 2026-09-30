"""Chat intent interpreter agent."""

import json
from typing import Any

from src.backend.infra.manage import openai, prompts


class ChatIntentAgent:
    def __init__(
        self,
        *,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.0,
    ) -> None:
        self.model = model
        self.temperature = temperature

    async def run(
        self,
        question: str,
        *,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        prompt = (
            prompts.interpreter_chat
            .replace("{{QUESTION}}", question)
            .replace("{{HISTORY}}", json.dumps(history or [], ensure_ascii=False, default=str))
        )
        response = await openai.send(
            prompt,
            model=self.model,
            temperature=self.temperature,
        )
        return response.output_text

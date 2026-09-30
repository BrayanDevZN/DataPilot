"""Generate dashboards and keep temporary analysis context in Redis."""

import asyncio
import json
from typing import Any
from uuid import UUID, uuid4

from src.backend.repository.cache import Cache
from src.backend.service.agents import (
    AnalysisAgent,
    DashboardPlannerAgent,
    MultiAnalysisAgent,
)
from src.backend.service.agents.tool import AgentDataTools


class DashboardContextStore:
    TTL_SECONDS = 30 * 60

    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    def _key(self, analysis_id: UUID | str) -> str:
        return f"dashboard_analysis:{analysis_id}"

    async def save(
        self,
        *,
        user_id: int,
        prompt: str | None,
        plan: dict[str, Any],
        schema: dict[str, Any],
        charts: list[dict[str, Any]],
        engine: str,
    ) -> str:
        analysis_id = str(uuid4())
        payload = {
            "user_id": user_id,
            "prompt": prompt,
            "plan": plan,
            "schema": schema,
            "charts": charts,
            "engine": engine,
        }

        await self.cache.set(
            self._key(analysis_id),
            json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            ),
            expire=self.TTL_SECONDS,
        )

        return analysis_id

    async def get(
        self,
        analysis_id: UUID | str,
        *,
        user_id: int,
    ) -> dict[str, Any] | None:
        result = await self.cache.get(
            self._key(analysis_id)
        )
        payload = result["value"]

        if payload is None:
            return None

        if isinstance(payload, bytes):
            payload = payload.decode()

        try:
            data = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return None

        if data.get("user_id") != user_id:
            return None

        return data


class DashboardAgentPipeline:
    def __init__(
        self,
        cache: Cache,
    ) -> None:
        self.contexts = DashboardContextStore(cache)
        self.planner = DashboardPlannerAgent()
        self.analysis = AnalysisAgent()
        self.multi_analysis = MultiAnalysisAgent()

    def _parse_plan(self, output: str) -> dict[str, Any]:
        text = str(output or "").strip()

        fence = chr(96) * 3
        if text.startswith(fence):
            lines = text.splitlines()
            if lines and lines[0].startswith(fence):
                lines = lines[1:]
            if lines and lines[-1].strip() == fence:
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            plan = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Dashboard planner returned invalid JSON"
            ) from error

        if not isinstance(plan, dict):
            raise ValueError(
                "Dashboard planner returned an invalid plan"
            )

        charts = plan.get("charts")
        if not isinstance(charts, list) or not charts:
            raise ValueError(
                "Dashboard planner did not return chart plans"
            )

        if len(charts) > 100:
            raise ValueError(
                "Dashboard planner returned too many charts"
            )

        return plan

    async def generate(
        self,
        data,
        *,
        user_id: int,
        prompt: str | None = None,
    ) -> dict[str, Any]:
        tools = await asyncio.to_thread(
            AgentDataTools,
            data,
        )
        schema = await asyncio.to_thread(
            tools.dataset_schema
        )

        plan_output = await self.planner.run(
            prompt,
            schema,
        )
        plan = self._parse_plan(plan_output)

        charts = await asyncio.to_thread(
            tools.execute_many,
            plan["charts"],
        )

        analysis_id = await self.contexts.save(
            user_id=user_id,
            prompt=prompt,
            plan=plan,
            schema=schema,
            charts=charts,
            engine=tools.engine,
        )

        return {
            "analysis_id": analysis_id,
            "charts": charts,
            "engine": tools.engine,
            "analysis_expires_in": self.contexts.TTL_SECONDS,
        }

    async def run_analysis(
        self,
        analysis_id: UUID | str,
        *,
        user_id: int,
        question: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str | None:
        context = await self.contexts.get(
            analysis_id,
            user_id=user_id,
        )

        if context is None:
            return None

        charts = context.get("charts") or []
        interpretation = {
            "plan": context.get("plan"),
            "schema": context.get("schema"),
            "dashboard_prompt": context.get("prompt"),
            "engine": context.get("engine"),
        }

        if len(charts) == 1:
            return await self.analysis.run(
                question=question,
                chart=charts[0],
                interpretation=interpretation,
                history=history,
            )

        return await self.multi_analysis.run(
            question=question,
            charts=charts,
            interpretation=interpretation,
            history=history,
        )

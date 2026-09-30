"""Chart changes are serialized by locking their parent dashboard."""

from typing import Any

from sqlalchemy import delete

from src.backend.logs.log import log_operation

from ..control_base import transactional, DashboardChildControl
from ..models import DashboardChart


class DashboardChartsControl(DashboardChildControl):
    model = DashboardChart

    @log_operation
    @transactional
    async def list_by_dashboard(self, dashboard_id: int, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self.list(filters={"dashboard_id": dashboard_id}, limit=limit, offset=offset)

    @log_operation
    @transactional
    async def replace_all(self, dashboard_id: int, charts: list[dict[str, Any]]) -> dict[str, Any]:
        self._require_transaction()
        if not charts:
            raise ValueError("Provide at least one chart")
        prepared = []
        for chart in charts:
            if set(chart) - {"chart_type", "title", "chart_data", "chart_config"}:
                raise ValueError("Unexpected chart fields")
            if not {"chart_type", "title", "chart_data"} <= set(chart):
                raise ValueError("Missing required chart fields")
            prepared.append(self._values({**chart, "dashboard_id": dashboard_id}))
        await self._lock_dashboard(dashboard_id)
        # Even if a caller catches an insert error, the previous charts survive.
        async with self.session.begin_nested():
            await self.session.execute(delete(self.table).where(self.table.c.dashboard_id == dashboard_id))
            items = [(await self.create(chart))["item"] for chart in prepared]
        return {"items": items, "count": len(items)}

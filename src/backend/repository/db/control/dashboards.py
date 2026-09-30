"""Dashboard operations, including atomic replacement of refresh results."""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update

from src.backend.logs.log import log_operation

from ..control_base import TableControl
from ..models import Dashboard, DashboardChart, DashboardChartSettings
from .dashboard_charts import DashboardChartsControl


class DashboardsControl(TableControl):
    model = Dashboard

    @log_operation
    async def list_by_user(self, user_id: int, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return await self.list(filters={"user_id": user_id}, limit=limit, offset=offset)

    @log_operation
    async def get_with_charts(self, dashboard_id: int, user_id: int) -> dict[str, Any]:
        # A parent lock keeps a concurrent refresh from mixing old and new charts.
        dashboard = await self._lock_dashboard(dashboard_id, owner_user_id=user_id)
        charts = (await self.session.execute(select(DashboardChart.__table__).where(
            DashboardChart.dashboard_id == dashboard_id,
        ).order_by(DashboardChart.id))).mappings().all()
        settings = (await self.session.execute(select(DashboardChartSettings.__table__).where(
            DashboardChartSettings.dashboard_id == dashboard_id,
        ).order_by(DashboardChartSettings.id))).mappings().all()
        dashboard["charts"] = [dict(chart) for chart in charts]
        dashboard["chart_settings"] = [dict(setting) for setting in settings]
        return {"found": True, "item": dashboard}

    @log_operation
    async def finish_refresh(self, dashboard_id: int, user_id: int,
                             expected_updated_at: datetime, charts: list[dict[str, Any]],
                             ai_suggestion: str, *, prompt: str | None = None) -> dict[str, Any]:
        current = await self._lock_dashboard(dashboard_id, owner_user_id=user_id)
        if current["updated_at"] != expected_updated_at:
            return {"updated": False, "item": None}
        async with self.session.begin_nested():
            replacement = await DashboardChartsControl(self.session).replace_all(dashboard_id, charts)
            values = {"ai_suggestion": ai_suggestion, "is_outdated": False}
            if prompt is not None:
                values["prompt"] = prompt
            result = await self.update(dashboard_id, values, filters={"user_id": user_id},
                                       expected={"updated_at": expected_updated_at})
            if not result["updated"]:
                raise RuntimeError("Dashboard version changed inside locked refresh")
        result["item"]["charts"] = replacement["items"]
        return result

    @log_operation
    async def mark_outdated_by_source(self, data_source_id: int) -> dict[str, Any]:
        self._require_transaction()
        # Deterministic order when several dashboard locks are acquired.
        ids = (await self.session.execute(select(self.table.c.id).where(
            self.table.c.data_source_id == data_source_id,
        ).order_by(self.table.c.id).with_for_update())).scalars().all()
        if not ids:
            return {"items": [], "count": 0}
        statement = update(self.table).where(self.table.c.id.in_(ids)).values(
            is_outdated=True, updated_at=func.clock_timestamp(),
        ).returning(*self.table.c)
        rows = (await self.session.execute(statement)).mappings().all()
        return {"items": [dict(row) for row in rows], "count": len(rows)}

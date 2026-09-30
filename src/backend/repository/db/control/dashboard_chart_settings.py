"""Serialized settings saves, including dashboard defaults with a NULL chart_id."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.backend.logs.log import log_operation

from ..control_base import transactional, DashboardChildControl, RecordNotFoundError
from ..models import DashboardChart, DashboardChartSettings


class DashboardChartSettingsControl(DashboardChildControl):
    model = DashboardChartSettings

    @log_operation
    @transactional
    async def save(self, dashboard_id: int, data: dict[str, Any], *, chart_id: int | None = None) -> dict[str, Any]:
        values = self._values(data, updating=True)
        await self._lock_dashboard(dashboard_id)
        columns = self.table.c
        if chart_id is not None:
            valid = select(DashboardChart.id).where(DashboardChart.id == chart_id, DashboardChart.dashboard_id == dashboard_id)
            if (await self.session.execute(valid)).scalar_one_or_none() is None:
                raise RecordNotFoundError("Chart not found in this dashboard")
            statement = insert(self.table).values(**values, dashboard_id=dashboard_id, chart_id=chart_id)
            statement = statement.on_conflict_do_update(
                index_elements=[columns.chart_id], set_=values,
            ).returning(*self.table.c)
        else:
            # A partial unique index covers the NULL chart_id case too.
            statement = insert(self.table).values(**values, dashboard_id=dashboard_id, chart_id=None)
            statement = statement.on_conflict_do_update(
                index_elements=[columns.dashboard_id], index_where=columns.chart_id.is_(None),
                set_=values,
            ).returning(*self.table.c)
        row = (await self.session.execute(statement)).mappings().one()
        return {"item": dict(row)}

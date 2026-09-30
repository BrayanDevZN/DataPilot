from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .dashboard_chart_settings import DashboardChartSettings
    from .dashboards import Dashboard


class DashboardChart(Base):
    __tablename__ = "dashboard_charts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id", ondelete="CASCADE"))
    chart_type: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    chart_data: Mapped[dict | list] = mapped_column(JSONB)
    chart_config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard", back_populates="charts", foreign_keys="DashboardChart.dashboard_id", lazy="raise",
    )

    settings: Mapped["DashboardChartSettings | None"] = relationship(
        "DashboardChartSettings", back_populates="chart", foreign_keys="DashboardChartSettings.chart_id",
        lazy="raise", passive_deletes="all", uselist=False,
    )

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .dashboard_charts import DashboardChart
    from .dashboards import Dashboard


class DashboardChartSettings(Base):
    __tablename__ = "dashboard_chart_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id", ondelete="CASCADE"))
    chart_id: Mapped[int | None] = mapped_column(ForeignKey("dashboard_charts.id", ondelete="CASCADE"), unique=True)
    chart_color: Mapped[str] = mapped_column(Text, server_default="#4f46e5")
    chart_background: Mapped[str] = mapped_column(Text, server_default="#f8fafc")
    x_axis_text_color: Mapped[str] = mapped_column(Text, server_default="#0f172a")
    y_axis_text_color: Mapped[str] = mapped_column(Text, server_default="#0f172a")
    grid_color: Mapped[str] = mapped_column(Text, server_default="#cbd5e1")
    grid_style: Mapped[str] = mapped_column(Text, server_default="3 3")
    bar_style: Mapped[str] = mapped_column(Text, server_default="rounded")
    pie_colors: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    show_legend: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("dashboard_chart_settings_dashboard_default_unique", dashboard_id,
              unique=True, postgresql_where=chart_id.is_(None)),
    )

    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard", back_populates="chart_settings", foreign_keys="DashboardChartSettings.dashboard_id", lazy="raise",
    )

    chart: Mapped["DashboardChart | None"] = relationship(
        "DashboardChart", back_populates="settings", foreign_keys="DashboardChartSettings.chart_id", lazy="raise",
    )

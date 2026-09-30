from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .collaboration_notifications import CollaborationNotification
    from .dashboard_chart_settings import DashboardChartSettings
    from .dashboard_charts import DashboardChart
    from .dashboard_collaborations import DashboardCollaboration
    from .data_sources import DataSource
    from .users import User


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, server_default=text("gen_random_uuid()"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text, server_default="")
    ai_suggestion: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(Text)
    data_source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id", ondelete="SET NULL"))
    is_outdated: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("dashboards_public_id_unique", public_id, unique=True),)

    user: Mapped["User"] = relationship(
        "User", back_populates="dashboards", foreign_keys="Dashboard.user_id", lazy="raise",
    )

    data_source: Mapped["DataSource | None"] = relationship(
        "DataSource", back_populates="dashboards", foreign_keys="Dashboard.data_source_id", lazy="raise",
    )

    charts: Mapped[list["DashboardChart"]] = relationship(
        "DashboardChart", back_populates="dashboard", foreign_keys="DashboardChart.dashboard_id",
        lazy="raise", passive_deletes="all",
    )

    chart_settings: Mapped[list["DashboardChartSettings"]] = relationship(
        "DashboardChartSettings", back_populates="dashboard", foreign_keys="DashboardChartSettings.dashboard_id",
        lazy="raise", passive_deletes="all",
    )

    collaborations: Mapped[list["DashboardCollaboration"]] = relationship(
        "DashboardCollaboration", back_populates="dashboard", foreign_keys="DashboardCollaboration.dashboard_id",
        lazy="raise", passive_deletes="all",
    )

    notifications: Mapped[list["CollaborationNotification"]] = relationship(
        "CollaborationNotification", back_populates="dashboard", foreign_keys="CollaborationNotification.dashboard_id",
        lazy="raise", passive_deletes="all",
    )

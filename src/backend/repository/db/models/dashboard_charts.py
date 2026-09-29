from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DashboardChart(Base):
    __tablename__ = "dashboard_charts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(ForeignKey("dashboards.id", ondelete="CASCADE"))
    chart_type: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    chart_data: Mapped[dict | list] = mapped_column(JSONB)
    chart_config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

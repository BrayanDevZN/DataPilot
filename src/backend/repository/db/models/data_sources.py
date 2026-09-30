from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

if TYPE_CHECKING:
    from .dashboards import Dashboard
    from .users import User


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text)
    file_data: Mapped[list[dict]] = mapped_column(JSONB)
    row_count: Mapped[int] = mapped_column(Integer)
    column_count: Mapped[int] = mapped_column(Integer)
    source_type: Mapped[str] = mapped_column(String(20), server_default="file")
    connection_config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    refresh_interval_days: Mapped[int | None] = mapped_column(Integer)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (CheckConstraint("source_type IN ('file', 'web', 'database')", name="data_sources_source_type_check"),)

    user: Mapped["User"] = relationship(
        "User", back_populates="data_sources", foreign_keys="DataSource.user_id", lazy="raise",
    )

    dashboards: Mapped[list["Dashboard"]] = relationship(
        "Dashboard", back_populates="data_source", foreign_keys="Dashboard.data_source_id",
        lazy="raise", passive_deletes="all",
    )

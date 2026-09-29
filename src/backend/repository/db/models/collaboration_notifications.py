from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class CollaborationNotification(Base):
    __tablename__ = "collaboration_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    collaboration_id: Mapped[int | None] = mapped_column(ForeignKey("dashboard_collaborations.id", ondelete="SET NULL"))
    dashboard_id: Mapped[int | None] = mapped_column(ForeignKey("dashboards.id", ondelete="SET NULL"))
    message: Mapped[str] = mapped_column(Text)
    notification_type: Mapped[str] = mapped_column(String(40))
    is_read: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("collaboration_notifications_user_idx", user_id, created_at.desc()),)

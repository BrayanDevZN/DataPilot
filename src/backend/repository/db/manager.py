"""Migration entry point and table controls sharing Redis and an async session."""

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.logs.log import logger, log_operation

from ..control import (
    ControlCollaborationNotifications,
    ControlConversations,
    ControlDashboardCharts,
    ControlDashboardChartSettings,
    ControlDashboardCollaborations,
    ControlDashboards,
    ControlDataSources,
    ControlMessages,
    ControlUsers,
    ControlValidationAccount,
    ControlValidation,
)
from .migrate import Migration

__all__ = ["ControlDb", "Migration"]


class ControlDb:
    """Group the cached table controls around Redis and the caller's AsyncSession."""

    @log_operation
    def __init__(self, redis: Redis, session: AsyncSession) -> None:
        if not isinstance(redis, Redis):
            raise TypeError("ControlDb requires an async Redis client")
        if not isinstance(session, AsyncSession):
            raise TypeError("ControlDb requires a SQLAlchemy AsyncSession")

        self.users = ControlUsers(redis, session)
        self.validation = ControlValidation(redis, session)
        self.validation_account = ControlValidationAccount(redis, session)
        self.conversations = ControlConversations(redis, session)
        self.messages = ControlMessages(redis, session)
        self.data_sources = ControlDataSources(redis, session)
        self.dashboards = ControlDashboards(redis, session)
        self.dashboard_charts = ControlDashboardCharts(redis, session)
        self.dashboard_chart_settings = ControlDashboardChartSettings(redis, session)
        self.dashboard_collaborations = ControlDashboardCollaborations(redis, session)
        self.collaboration_notifications = ControlCollaborationNotifications(redis, session)

        logger.info("Controles das 11 tabelas inicializados com Redis e a mesma AsyncSession")

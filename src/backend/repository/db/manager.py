"""Migration entry point and table controls sharing one async session."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.logs.log import logger, log_operation

from .control import (
    CollaborationNotificationsControl,
    ConversationsControl,
    DashboardChartsControl,
    DashboardChartSettingsControl,
    DashboardCollaborationsControl,
    DashboardsControl,
    DataSourcesControl,
    MessagesControl,
    UsersControl,
    ValidationAccountControl,
    ValidationControl,
)
from .migrate import Migration

__all__ = ["ControlDb", "Migration"]


class ControlDb:
    """Group every table control around the caller's AsyncSession."""

    @log_operation
    def __init__(self, session: AsyncSession) -> None:
        if not isinstance(session, AsyncSession):
            raise TypeError("ControlDb requires a SQLAlchemy AsyncSession")

        self.users = UsersControl(session)
        self.validation = ValidationControl(session)
        self.validation_account = ValidationAccountControl(session)
        self.conversations = ConversationsControl(session)
        self.messages = MessagesControl(session)
        self.data_sources = DataSourcesControl(session)
        self.dashboards = DashboardsControl(session)
        self.dashboard_charts = DashboardChartsControl(session)
        self.dashboard_chart_settings = DashboardChartSettingsControl(session)
        self.dashboard_collaborations = DashboardCollaborationsControl(session)
        self.collaboration_notifications = CollaborationNotificationsControl(session)

        logger.info("Controles das 11 tabelas inicializados com a mesma AsyncSession")

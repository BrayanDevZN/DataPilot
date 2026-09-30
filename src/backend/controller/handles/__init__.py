from .agents import router as agents_router
from .auth import router as auth_router
from .collaboration_notifications import router as collaboration_notifications_router
from .conversations import router as conversations_router
from .dashboard_chart_settings import router as dashboard_chart_settings_router
from .dashboard_charts import router as dashboard_charts_router
from .dashboard_collaborations import router as dashboard_collaborations_router
from .dashboards import router as dashboards_router
from .data_sources import router as data_sources_router
from .messages import router as messages_router
from .sender import router as sender_router
from .users import router as users_router


routers = (
    agents_router,
    auth_router,
    users_router,
    conversations_router,
    messages_router,
    sender_router,
    data_sources_router,
    dashboards_router,
    dashboard_charts_router,
    dashboard_chart_settings_router,
    dashboard_collaborations_router,
    collaboration_notifications_router,
)

PUBLIC_ROUTES = {
    "/auth",
    "/auth/refresh",
    "/auth/logout",
    "/users",
    "/sender/create-account",
    "/sender/change-password",
    "/sender/auth2",
}

__all__ = [
    "routers",
    "agents_router",
    "auth_router",
    "PUBLIC_ROUTES",
    "users_router",
    "conversations_router",
    "messages_router",
    "sender_router",
    "data_sources_router",
    "dashboards_router",
    "dashboard_charts_router",
    "dashboard_chart_settings_router",
    "dashboard_collaborations_router",
    "collaboration_notifications_router",
]

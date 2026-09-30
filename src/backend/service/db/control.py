"""Service-level table controls."""

from .table.collaboration_notifications import CollaborationNotifications
from .table.conversations import Conversations
from .table.dashboard_chart_settings import DashboardChartSettings
from .table.dashboard_charts import DashboardCharts
from .table.dashboard_collaborations import DashboardCollaborations
from .table.dashboards import Dashboards
from .table.data_sources import DataSources
from .table.messages import Messages
from .table.users import Users
from .table.validation import Validation
from .table.validation_account import ValidationAccount


class ControlDb:
    def __init__(self) -> None:
        self.users = Users()
        self.validation = Validation()
        self.validation_account = ValidationAccount()
        self.conversations = Conversations()
        self.messages = Messages()
        self.data_sources = DataSources()
        self.dashboards = Dashboards()
        self.dashboard_charts = DashboardCharts()
        self.dashboard_chart_settings = DashboardChartSettings()
        self.dashboard_collaborations = DashboardCollaborations()
        self.collaboration_notifications = CollaborationNotifications()


control_db = ControlDb()

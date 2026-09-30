from .base import CachedControl
from ..db.control.dashboard_chart_settings import DashboardChartSettingsControl


class ControlDashboardChartSettings(CachedControl):
    controller = DashboardChartSettingsControl

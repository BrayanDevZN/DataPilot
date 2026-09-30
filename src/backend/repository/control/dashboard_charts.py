from .base import CachedControl
from ..db.control.dashboard_charts import DashboardChartsControl


class ControlDashboardCharts(CachedControl):
    controller = DashboardChartsControl

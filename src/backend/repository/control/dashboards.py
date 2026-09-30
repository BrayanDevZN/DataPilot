from .base import CachedControl
from ..db.control.dashboards import DashboardsControl


class ControlDashboards(CachedControl):
    controller = DashboardsControl

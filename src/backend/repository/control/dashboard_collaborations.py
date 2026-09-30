from .base import CachedControl
from ..db.control.dashboard_collaborations import DashboardCollaborationsControl


class ControlDashboardCollaborations(CachedControl):
    controller = DashboardCollaborationsControl

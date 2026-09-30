from .base import CachedControl
from ..db.control.collaboration_notifications import CollaborationNotificationsControl


class ControlCollaborationNotifications(CachedControl):
    controller = CollaborationNotificationsControl

from .base import CachedControl
from ..db.control.messages import MessagesControl


class ControlMessages(CachedControl):
    controller = MessagesControl

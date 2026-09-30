from .base import CachedControl
from ..db.control.conversations import ConversationsControl


class ControlConversations(CachedControl):
    controller = ConversationsControl

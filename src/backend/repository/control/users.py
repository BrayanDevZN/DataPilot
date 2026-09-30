from .base import CachedControl
from ..db.control.users import UsersControl


class ControlUsers(CachedControl):
    controller = UsersControl

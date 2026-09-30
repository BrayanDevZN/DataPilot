from .base import CachedControl
from ..db.control.validation_account import ValidationAccountControl


class ControlValidationAccount(CachedControl):
    controller = ValidationAccountControl

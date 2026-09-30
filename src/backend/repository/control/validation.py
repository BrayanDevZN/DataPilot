from .base import CachedControl
from ..db.control.validation import ValidationControl


class ControlValidation(CachedControl):
    controller = ValidationControl

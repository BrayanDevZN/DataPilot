from .base import CachedControl
from ..db.control.data_sources import DataSourcesControl


class ControlDataSources(CachedControl):
    controller = DataSourcesControl

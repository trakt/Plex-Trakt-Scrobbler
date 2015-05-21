from plugin.sync.core.enums import SyncData
from plugin.sync.handlers.core.base import DataHandler


class Ratings(DataHandler):
    data = SyncData.Ratings

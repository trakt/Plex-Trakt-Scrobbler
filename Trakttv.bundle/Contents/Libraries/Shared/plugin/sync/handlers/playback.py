from plugin.sync.core.enums import SyncData
from plugin.sync.handlers.core.base import DataHandler


class Playback(DataHandler):
    data = SyncData.Playback

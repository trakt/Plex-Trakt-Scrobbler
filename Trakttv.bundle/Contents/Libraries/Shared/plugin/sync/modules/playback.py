from plugin.sync import SyncData
from plugin.sync.modules.core.base import SyncModule


class Playback(SyncModule):
    __data__ = SyncData.Playback

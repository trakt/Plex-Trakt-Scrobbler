from plugin.sync import SyncData
from plugin.sync.modules.core.base import SyncModule


class Watched(SyncModule):
    __data__ = SyncData.Watched

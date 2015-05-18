from plugin.sync import SyncData
from plugin.sync.modules.core.base import SyncModule


class Ratings(SyncModule):
    __data__ = SyncData.Ratings

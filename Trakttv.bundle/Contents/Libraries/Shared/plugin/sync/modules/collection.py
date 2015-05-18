from plugin.sync import SyncData
from plugin.sync.modules.core.base import SyncModule


class Collection(SyncModule):
    __data__ = SyncData.Collection

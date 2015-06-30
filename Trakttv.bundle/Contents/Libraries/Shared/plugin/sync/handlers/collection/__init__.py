from plugin.sync import SyncData
from plugin.sync.handlers.core.base.mode import ModeHandler
from plugin.sync.handlers.collection.pull import Pull
from plugin.sync.handlers.collection.push import Push


class Collection(ModeHandler):
    data = SyncData.Collection
    children = [
        Pull,
        Push
    ]

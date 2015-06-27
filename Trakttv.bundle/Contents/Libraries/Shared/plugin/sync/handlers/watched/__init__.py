from plugin.sync import SyncData
from plugin.sync.handlers.core.base.mode import ModeHandler
from plugin.sync.handlers.watched.pull import Pull
from plugin.sync.handlers.watched.push import Push


class Watched(ModeHandler):
    data = SyncData.Watched
    children = [
        Pull,
        Push
    ]

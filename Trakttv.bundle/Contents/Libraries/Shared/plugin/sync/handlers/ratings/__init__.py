from plugin.sync import SyncData
from plugin.sync.handlers.core.base.mode import ModeHandler
from plugin.sync.handlers.ratings.pull import Pull
from plugin.sync.handlers.ratings.push import Push


class Ratings(ModeHandler):
    data = SyncData.Ratings
    children = [
        Pull,
        Push
    ]

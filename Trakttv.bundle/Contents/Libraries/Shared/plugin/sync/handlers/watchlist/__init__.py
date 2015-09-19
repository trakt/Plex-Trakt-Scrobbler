from plugin.sync.core.enums import SyncData
from plugin.sync.handlers.core.base.mode import ModeHandler
from plugin.sync.handlers.watchlist.pull import Pull


class Watchlist(ModeHandler):
    data = SyncData.Watchlist
    children = [
        Pull
    ]

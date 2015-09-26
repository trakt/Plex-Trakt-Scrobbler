from plugin.sync.core.enums import SyncData
from plugin.sync.handlers.core.base.mode import ModeHandler
from plugin.sync.handlers.list.pull import Pull


class List(ModeHandler):
    data = [
        SyncData.Liked,
        SyncData.Personal,
        SyncData.Watchlist
    ]

    children = [
        Pull
    ]

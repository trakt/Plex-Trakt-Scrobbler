from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncWatchlistInterface(Get, Add, Remove):
    path = 'sync/watchlist'
    flags = {'in_watchlist': True}

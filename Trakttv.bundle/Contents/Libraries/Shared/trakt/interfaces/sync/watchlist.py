from trakt.interfaces.sync.base import SyncBaseInterface


class SyncWatchlistInterface(SyncBaseInterface):
    path = 'sync/watchlist'
    flags = {'in_watchlist': True}

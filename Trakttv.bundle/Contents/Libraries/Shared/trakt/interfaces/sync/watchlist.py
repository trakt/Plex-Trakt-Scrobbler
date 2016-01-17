from trakt.interfaces.base import authenticated
from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncWatchlistInterface(Get, Add, Remove):
    path = 'sync/watchlist'
    flags = {'in_watchlist': True}

    @authenticated
    def seasons(self, store=None, **kwargs):
        return self.get(
            'seasons',
            store,
            **kwargs
        )

    @authenticated
    def episodes(self, store=None, **kwargs):
        return self.get(
            'episodes',
            store,
            **kwargs
        )

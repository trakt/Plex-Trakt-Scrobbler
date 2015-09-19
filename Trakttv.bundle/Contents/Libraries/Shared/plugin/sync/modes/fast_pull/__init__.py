from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode
from plugin.sync.modes.fast_pull.movies import Movies
from plugin.sync.modes.fast_pull.shows import Shows
from plugin.sync.modes.fast_pull.watchlist import Watchlist

import elapsed
import logging

log = logging.getLogger(__name__)


class FastPull(Mode):
    mode = SyncMode.FastPull

    children = [
        Movies,
        Shows,
        Watchlist
    ]

    @elapsed.clock
    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Run children
        self.execute_children()

from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.core.base import Mode
from plugin.sync.modes.fast_pull.lists import LikedLists, PersonalLists, Watchlist
from plugin.sync.modes.fast_pull.movies import Movies
from plugin.sync.modes.fast_pull.shows import Shows

import elapsed
import logging

log = logging.getLogger(__name__)


class FastPull(Mode):
    data = SyncData.All
    mode = SyncMode.FastPull

    children = [
        Movies,
        Shows,

        LikedLists,
        PersonalLists,
        Watchlist
    ]

    @elapsed.clock
    def construct(self):
        # Start progress tracking
        self.current.progress.start()

        # Construct children
        self.execute_children('construct')

    @elapsed.clock
    def start(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Start children
        self.execute_children('start')

    @elapsed.clock
    def run(self):
        # Run children
        self.execute_children('run')

    @elapsed.clock
    def stop(self):
        # Stop children
        self.execute_children('stop')

        # Stop progress tracking
        self.current.progress.stop()

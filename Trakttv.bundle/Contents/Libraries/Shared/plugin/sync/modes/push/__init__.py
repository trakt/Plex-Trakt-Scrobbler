from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.core.base import Mode
from plugin.sync.modes.push.movies import Movies
from plugin.sync.modes.push.shows import Shows

import elapsed


class Push(Mode):
    data = SyncData.All
    mode = SyncMode.Push

    children = [
        Movies,
        Shows
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
        with self.plex.prime():
            # Run children
            self.execute_children('run')

    @elapsed.clock
    def finish(self):
        # Run children
        self.execute_children('finish')

        # Send artifacts to trakt
        self.current.artifacts.send()

    @elapsed.clock
    def stop(self):
        # Stop children
        self.execute_children('stop')

        # Stop progress tracking
        self.current.progress.stop()

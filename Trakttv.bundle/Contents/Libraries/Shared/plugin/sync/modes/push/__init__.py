from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode
from plugin.sync.modes.push.movies import Movies
from plugin.sync.modes.push.shows import Shows

import elapsed


class Push(Mode):
    mode = SyncMode.Push

    children = [
        Movies,
        Shows
    ]

    @elapsed.clock
    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        with self.plex.prime():
            # Run children
            self.execute_children()

        # Send artifacts to trakt
        self.current.artifacts.send()

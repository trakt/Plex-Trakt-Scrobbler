from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode
from plugin.sync.modes.pull.movies import Movies
from plugin.sync.modes.pull.shows import Shows

import elapsed
import logging

log = logging.getLogger(__name__)


class Pull(Mode):
    mode = SyncMode.Pull

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

        # Run children
        self.execute_children()

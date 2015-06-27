from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode


class Full(Mode):
    mode = SyncMode.Full

    def run(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Run fast pull
        self.modes[SyncMode.FastPull].execute_children()

        # Run push
        self.modes[SyncMode.Push].execute_children()

        # Send artifacts to trakt
        self.current.artifacts.send()

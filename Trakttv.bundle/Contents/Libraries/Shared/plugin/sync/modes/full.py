from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.modes.core.base import Mode

import elapsed


class Full(Mode):
    data = SyncData.All
    mode = SyncMode.Full

    @elapsed.clock
    def construct(self):
        # Start progress tracking
        self.current.progress.start()

        # Construct children
        self.modes[SyncMode.FastPull].execute_children('construct')
        self.modes[SyncMode.Push].execute_children('construct')

    @elapsed.clock
    def start(self):
        # Fetch changes from trakt.tv
        self.trakt.refresh()

        # Build key table for lookups
        self.trakt.build_table()

        # Start children
        self.modes[SyncMode.FastPull].execute_children('start')
        self.modes[SyncMode.Push].execute_children('start')

    @elapsed.clock
    def run(self):
        with self.plex.prime():
            # Run children
            self.modes[SyncMode.FastPull].execute_children('run')
            self.modes[SyncMode.Push].execute_children('run')

    @elapsed.clock
    def finish(self):
        # Run children
        self.modes[SyncMode.FastPull].execute_children('finish')
        self.modes[SyncMode.Push].execute_children('finish')

        # Send artifacts to trakt
        self.current.artifacts.send()

    @elapsed.clock
    def stop(self):
        # Stop children
        self.modes[SyncMode.FastPull].execute_children('stop')
        self.modes[SyncMode.Push].execute_children('stop')

        # Stop progress tracking
        self.current.progress.stop()

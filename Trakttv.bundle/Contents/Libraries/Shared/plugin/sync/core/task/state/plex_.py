from plugin.modules.core.manager import ModuleManager

from plex_database.library import Library
import elapsed
import logging

log = logging.getLogger(__name__)


class SyncStatePlex(object):
    def __init__(self, state):
        self.state = state
        self.task = state.task

        # Initialize plex.database.py
        self.library = Library(ModuleManager['matcher'].database)

    def load(self):
        # Ensure matcher configuration is up to date
        ModuleManager['matcher'].configure()

    @elapsed.clock
    def prime(self):
        return ModuleManager['matcher'].prime(force=True)

    @elapsed.clock
    def flush(self):
        with elapsed.clock(SyncStatePlex, 'flush:matcher'):
            log.debug('Flushing matcher cache...')

            # Flush matcher cache to disk
            ModuleManager['matcher'].flush(force=True)

from plugin.core.cache import CacheManager

from plex import Plex
from plex_database.library import Library
from plex_database.matcher import Matcher
import elapsed
import logging

log = logging.getLogger(__name__)


class SyncStatePlex(object):
    def __init__(self, state):
        self.state = state
        self.task = state.task

        # Retrieve matcher cache
        self.matcher_cache = CacheManager.get('plex.matcher')

        # Initialize plex.database.py
        self.matcher = Matcher(self.matcher_cache, Plex.client)
        self.library = Library(self.matcher)

    def load(self):
        pass

    @elapsed.clock
    def prime(self):
        return self.matcher_cache.prime(force=True)

    @elapsed.clock
    def flush(self):
        with elapsed.clock(SyncStatePlex, 'flush:matcher'):
            log.debug('Flushing matcher cache...')

            # Flush matcher cache to disk
            self.matcher_cache.flush(force=True)

from plugin.core.cache import CacheManager

from plex import Plex
from plex_database.library import Library
from plex_database.matcher import Matcher
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

    def flush(self):
        log.debug('Flushing matcher cache...')

        # Flush matcher cache to disk
        self.matcher_cache.flush(force=True)

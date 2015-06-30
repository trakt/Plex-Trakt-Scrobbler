from plugin.core.database import Database

from plex import Plex
from plex_database.library import Library
from plex_database.matcher import Matcher
from stash import ApswArchive, Stash
import logging

log = logging.getLogger(__name__)


class SyncStatePlex(object):
    def __init__(self, state):
        self.state = state
        self.task = state.task

        self.matcher_cache = Stash(
            ApswArchive(Database.cache('plex'), 'matcher'),
            'lru:///?capacity=500&compact_threshold=1500',
            'msgpack:///'
        )

        # Initialize plex.database.py
        self.matcher = Matcher(self.matcher_cache, Plex.client)
        self.library = Library(self.matcher)

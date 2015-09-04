from plugin.core.database import Database

from stash import ApswArchive
from trakt_sync.cache.backends import StashBackend
from trakt_sync.cache.main import Cache
from trakt_sync.differ.core.base import KEY_AGENTS
import logging

log = logging.getLogger(__name__)


class SyncStateTrakt(object):
    def __init__(self, state):
        self.state = state
        self.task = state.task

        self.cache = self._build_cache()

        self.changes = None
        self.table = None

        self.movies = None
        self.shows = None
        self.episodes = None

        # Parse data/media enums into lists
        self._data = [
            Cache.Data.get(d)
            for d in Cache.Data.parse(self.task.data)
        ]

        self._media = [
            Cache.Media.get(m)
            for m in Cache.Media.parse(self.task.media)
        ]

    def _build_cache(self):
        def storage(name):
            return StashBackend(
                ApswArchive(Database.cache('trakt'), name),
                'lru:///?capacity=500&compact_threshold=1500',
                'pickle:///?protocol=2'
            )

        return Cache(self.task.media, self.task.data, storage)

    def __getitem__(self, (media, data)):
        media = Cache.Media.get(media)
        data = Cache.Data.get(data)

        return self.cache[(self.task.account.trakt.username, media, data)]

    def invalidate(self, media, data):
        """Invalidate collection in trakt cache"""
        username = self.task.account.trakt.username

        # Invalidate collection
        self.cache.invalidate(username, media, data)

        log.debug('Invalidated trakt cache (%r, %r) for account: %r', media, data, username)

    def refresh(self):
        # Task checkpoint
        self.task.checkpoint()

        # Refresh cache for account, store changes
        self.changes = self.cache.refresh(self.task.account.trakt.username)
        self.table = None

        self.movies = None
        self.shows = None
        self.episodes = None

    def build_table(self):
        # Resolve changes
        self.changes = list(self.changes)

        # Map item `keys` into a table
        self.table = {}

        self.movies = set()
        self.shows = set()
        self.episodes = {}

        log.debug('Building table...')

        for key in self.cache.collections:
            username, media, data = key

            if username != self.task.account.trakt.username:
                # Collection isn't for the current account
                continue

            if media not in self._media:
                log.debug('Media %r has not been enabled [enabled: %r]', data, self._media)
                continue

            if data not in self._data:
                log.debug('Data %r has not been enabled [enabled: %r]', data, self._data)
                continue

            log.debug('[%-31s] Building table from collection...', '/'.join(key))

            # Retrieve key map
            if media == 'movies':
                keys = self.movies
            elif media in ['shows', 'seasons', 'episodes']:
                keys = self.shows
            else:
                raise ValueError('Unknown media type: %r', media)

            # Retrieve cache store
            store = self.cache[key]

            for pk, item in store.iteritems():
                # Store `pk` in `keys
                keys.add(pk)

                # Map `item.keys` -> `pk`
                for key in item.keys:
                    agent, _ = key

                    if agent not in KEY_AGENTS:
                        continue

                    if key in self.table:
                        continue

                    self.table[key] = pk

                # Map episodes in show
                if media == 'episodes':
                    if pk not in self.episodes:
                        self.episodes[pk] = set()

                    for identifier, _ in item.episodes():
                        self.episodes[pk].add(identifier)

            # Task checkpoint
            self.task.checkpoint()

        log.debug('Built table with %d keys (%d movies, %d shows)', len(self.table), len(self.movies), len(self.shows))

    def flush(self):
        # Flush trakt cache to disk
        self.cache.collections.flush()

        for key, store in self.cache.stores.items():
            log.debug('[%-31s] Flushing collection...', '/'.join(key))

            store.flush()

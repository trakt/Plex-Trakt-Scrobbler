from plugin.core.database import Database

from stash import ApswArchive
from trakt_sync.cache.backends import StashBackend
from trakt_sync.cache.main import Cache
from trakt_sync.differ.core.base import KEY_AGENTS
import elapsed
import logging

log = logging.getLogger(__name__)


class SyncStateTrakt(object):
    def __init__(self, state):
        self.state = state
        self.task = state.task

        self.cache = None

        self.changes = None
        self.table = None

        self.movies = None
        self.shows = None
        self.episodes = None

        self._data = None
        self._media = None

    def load(self):
        self.cache = self._build_cache()

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

    @elapsed.clock
    def refresh(self):
        # Task checkpoint
        self.task.checkpoint()

        # Refresh cache for account, store changes
        self.changes = self.cache.refresh(self.task.account.trakt.username)
        self.table = None

        self.movies = None
        self.shows = None
        self.episodes = None

    @elapsed.clock
    def build_table(self):
        # Resolve changes
        self.changes = list(self.changes)

        # Map item `keys` into a table
        self.table = {}

        self.movies = set()
        self.shows = set()
        self.episodes = {}

        log.debug('Building table...')

        log.debug(' - Data: %s', ', '.join([
            '/'.join(x) if type(x) is tuple else x
            for x in self._data
        ]))

        log.debug(' - Media: %s', ', '.join([
            '/'.join(x) if type(x) is tuple else x
            for x in self._media
        ]))

        for key in self.cache.collections:
            if len(key) == 3:
                # Sync
                username, media, data = key
            elif len(key) == 4:
                # Lists
                username = key[0]
                media = None
                data = tuple(key[1:3])
            else:
                log.warn('Unknown key: %r', key)
                continue

            if username != self.task.account.trakt.username:
                # Collection isn't for the current account
                continue

            if media and media not in self._media:
                log.debug('[%-31s] Media %r has not been enabled', '/'.join(key), data)
                continue

            if data not in self._data:
                log.debug('[%-31s] Data %r has not been enabled', '/'.join(key), data)
                continue

            # Retrieve key map
            keys = None

            if media == 'movies':
                keys = self.movies
            elif media in ['shows', 'seasons', 'episodes']:
                keys = self.shows
            elif not media:
                # Ignore unsupported media types
                continue
            else:
                log.warn('Unknown media type: %r', media)
                continue

            log.debug('[%-31s] Building table from collection...', '/'.join(key))

            # Retrieve cache store
            store = self.cache[key]

            for pk, item in store.iteritems():
                # Store `pk` in `keys
                if keys is not None:
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

        log.debug(
            'Built table with %d keys (movies: %d, shows: %d, episodes: %d)',
            len(self.table),
            len(self.movies),
            len(self.shows),
            len(self.episodes)
        )

    @elapsed.clock
    def flush(self):
        with elapsed.clock(SyncStateTrakt, 'flush:collections'):
            # Flush trakt collections to disk
            self.cache.collections.flush()

        with elapsed.clock(SyncStateTrakt, 'flush:stores'):
            # Flush trakt stores to disk
            for key, store in self.cache.stores.items():
                log.debug('[%-31s] Flushing collection...', '/'.join(key))

                store.flush()

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

    def build_table(self):
        # Resolve changes
        self.changes = list(self.changes)

        # Map item `keys` into a table
        self.table = {}

        log.debug('Building table...')

        for key in self.cache.collections:
            username, _, _ = key

            if username != self.task.account.trakt.username:
                # Collection isn't for the current account
                continue

            log.debug('[%-31s] Building table from collection...', '/'.join(key))

            # Retrieve cache store
            store = self.cache[key]

            for pk, item in store.iteritems():
                # Map `item.keys` -> `pk`
                for key in item.keys:
                    agent, _ = key

                    if agent not in KEY_AGENTS:
                        continue

                    if key in self.table:
                        continue

                    self.table[key] = pk

            # Task checkpoint
            self.task.checkpoint()

        log.debug('Built table with %d keys', len(self.table))

    def flush(self):
        # Flush trakt cache to disk
        self.cache.collections.flush()

        for key, store in self.cache.stores.items():
            log.debug('[%-31s] Flushing collection...', '/'.join(key))

            store.flush()

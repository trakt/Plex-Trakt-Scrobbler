from plugin.core.helpers.variable import try_convert
from plugin.core.backup import BackupManager
from plugin.core.constants import GUID_SERVICES
from plugin.core.database.manager import DatabaseManager
from plugin.core.exceptions import AccountAuthenticationError

from plex.objects.library import metadata as plex_objects
from stash import ApswArchive
from trakt import objects as trakt_objects
from trakt_sync.cache.backends import StashBackend
from trakt_sync.cache.main import Cache
import elapsed
import logging
import os

IGNORED_DATA = [
    Cache.Data.get(Cache.Data.Liked),
    Cache.Data.get(Cache.Data.Personal)
]

log = logging.getLogger(__name__)


class SyncStateTrakt(object):
    def __init__(self, state):
        self.state = state
        self.task = state.task

        self.cache = None

        self.changes = None
        self.table = Table(self.task)

    def load(self):
        # Construct cache
        self.cache = self._build_cache()

        # Load table handler
        self.table.load()

    def _build_cache(self):
        def storage(name):
            return StashBackend(
                ApswArchive(DatabaseManager.cache('trakt'), name),
                'lru:///?capacity=500&compact_threshold=1500',
                'pickle:///?protocol=2'
            )

        cache = Cache(self.task.media, self.task.data, storage)

        # Bind to cache events
        cache.events.on([
            'refresh.sync.progress',
            'refresh.list.progress'
        ], self.on_refresh_progress)

        return cache

    def on_refresh_progress(self, source, current):
        # Step refresh progress for `source`
        self.task.progress.group(SyncStateTrakt, 'refresh:%s' % source).step()

    def __getitem__(self, key):
        collection = [
            self.task.account.trakt.username,
            Cache.Media.get(key[0]),
            Cache.Data.get(key[1])
        ]

        if len(key) > 2:
            # Include extra parameters (list id)
            collection.extend(key[2:])

        return self.cache[collection]

    def invalidate(self, *key):
        """Invalidate collection in trakt cache"""
        username = self.task.account.trakt.username

        # Invalidate collection
        self.cache.invalidate([username] + list(key))

        log.debug('Invalidated trakt cache %r for account: %r', key, username)

    @elapsed.clock
    def refresh(self):
        account = self.task.account

        if not account.trakt or not account.trakt.username:
            raise AccountAuthenticationError("Trakt account hasn't been authenticated")

        # Task checkpoint
        self.task.checkpoint()

        # Construct progress groups
        def setup_progress_group(source):
            # Retrieve steps from cache source
            steps = self.cache.source(source).steps()

            # Setup progress group with total steps
            self.task.progress.group(SyncStateTrakt, 'refresh:%s' % source).add(steps)

        setup_progress_group('list')
        setup_progress_group('sync')

        # Refresh cache for account, store changes
        self.changes = self.cache.refresh(account.trakt.username)

        # Resolve changes
        self.changes = list(self.changes)

        # Reset current table
        self.table.reset()

    @elapsed.clock
    def build_table(self):
        # Build table from cache
        self.table.build(self.cache)

    @elapsed.clock
    def flush(self):
        with elapsed.clock(SyncStateTrakt, 'flush:collections'):
            # Flush trakt collections to disk
            self.cache.collections.flush()

        with elapsed.clock(SyncStateTrakt, 'flush:stores'):
            # Flush trakt stores to disk
            for key, store in self.cache.stores.items():
                log.debug('[%-38s] Flushing collection...', '/'.join(key))

                store.flush()

        # Store backup of trakt data
        group = os.path.join('trakt', str(self.task.account.id))

        BackupManager.database.backup(group, DatabaseManager.cache('trakt'), self.task.id, {
            'account': {
                'id': self.task.account.id,
                'name': self.task.account.name,

                'trakt': {
                    'username': self.task.account.trakt.username
                }
            }
        })


class Table(object):
    def __init__(self, task):
        self.task = task

        self.movies = None
        self.shows = None

        self.movie_keys = None
        self.show_keys = None
        self.episode_keys = None

        self._data = None
        self._media = None

    def load(self):
        # Parse data/media enums into lists
        self._data = [
            Cache.Data.get(d)
            for d in Cache.Data.parse(self.task.data)
        ]

        self._media = [
            Cache.Media.get(m)
            for m in Cache.Media.parse(self.task.media)
        ]

    def reset(self):
        self.movies = None
        self.shows = None

        self.movie_keys = None
        self.show_keys = None
        self.episode_keys = None

    def build(self, cache):
        # Map item `keys` into tables
        self.movies = {}
        self.shows = {}

        self.movie_keys = set()
        self.show_keys = set()
        self.episode_keys = {}

        log.debug('Building tables...')

        log.debug(' - Data: %s', ', '.join([
            '/'.join(x) if type(x) is tuple else x
            for x in self._data
        ]))

        log.debug(' - Media: %s', ', '.join([
            '/'.join(x) if type(x) is tuple else x
            for x in self._media
        ]))

        # Construct progress group
        self.task.progress.group(Table, 'build').add(len(cache.collections))

        # Map each item in cache collections
        for key in cache.collections:
            # Increment one step
            self.task.progress.group(Table, 'build').step()

            # Parse `key`
            if len(key) == 3:
                # Sync
                username, media, data = key
            elif len(key) == 4:
                # Lists
                username, media, data = tuple(key[0:3])
            else:
                log.warn('Unknown key: %r', key)
                continue

            if username != self.task.account.trakt.username:
                # Collection isn't for the current account
                continue

            if media and media not in self._media:
                log.debug('[%-38s] Media %r has not been enabled', '/'.join(key), media)
                continue

            if data not in self._data:
                log.debug('[%-38s] Data %r has not been enabled', '/'.join(key), data)
                continue

            # Map store items
            if data not in IGNORED_DATA:
                self.map_items(key, cache[key], media)

        log.debug(
            'Built tables with %d keys (movies: %d, shows: %d, episodes: %d)',
            len(self.movies) + len(self.shows),
            len(self.movie_keys),
            len(self.show_keys),
            len(self.episode_keys)
        )

    def map_items(self, key, store, media=None):
        # Retrieve key map
        if media is not None:
            keys = self.keys(media)
            table = self.table(media)

            if keys is None or table is None:
                log.debug('[%-38s] Collection has been ignored (unknown/unsupported media)', '/'.join(key))
                return
        else:
            keys = None
            table = None

        # Map each item in store
        log.debug('[%-38s] Building table from collection...', '/'.join(key))

        for pk, item in store.iteritems():
            # Trim `pk` season/episode values
            if len(pk) > 2:
                pk = tuple(pk[:2])

            if pk[0] not in GUID_SERVICES:
                log.info('Ignoring item %r with an unknown primary agent: %r', item, pk)
                continue

            # Detect media type from `item`
            if media is not None:
                i_media = media
                i_keys = keys
                i_table = table
            else:
                i_media = self.media(item)
                i_keys = self.keys(i_media)
                i_table = self.table(i_media)

            # Store `pk` in `keys
            if i_keys is not None:
                i_keys.add(pk)

            # Map `item.keys` -> `pk`
            for key in item.keys:
                # Expand `key`
                if type(key) is not tuple or len(key) != 2:
                    continue

                service, id = key

                # Check if agent is supported
                if service not in GUID_SERVICES:
                    continue

                # Cast service id to integer
                if service in ['tvdb', 'tmdb', 'tvrage']:
                    id = try_convert(id, int, id)

                # Store key in table
                key = (service, id)

                if key in i_table:
                    continue

                i_table[key] = pk

            # Map episodes in show
            if i_media == 'episodes':
                if type(item) is trakt_objects.Show:
                    if pk not in self.episode_keys:
                        self.episode_keys[pk] = set()

                    for identifier, _ in item.episodes():
                        self.episode_keys[pk].add(identifier)
                elif type(item) is trakt_objects.Episode:
                    # TODO
                    pass
                else:
                    log.debug('Unknown episode item: %r', item)

        # Task checkpoint
        self.task.checkpoint()

    def keys(self, media):
        if type(media) is not str:
            media = self.media(media)

        if media == 'movies':
            return self.movie_keys

        if media in ['shows', 'seasons', 'episodes']:
            return self.show_keys

        log.warn('Unknown media: %r', media)
        return None

    @staticmethod
    def media(item):
        if type(item) is not type:
            i_type = type(item)
        else:
            i_type = item

        if issubclass(i_type, (trakt_objects.Movie, plex_objects.Movie)):
            return 'movies'

        if issubclass(i_type, (trakt_objects.Show, plex_objects.Show)):
            return 'shows'

        if issubclass(i_type, (trakt_objects.Season, plex_objects.Season)):
            return 'seasons'

        if issubclass(i_type, (trakt_objects.Episode, plex_objects.Episode)):
            return 'episodes'

        log.warn('Unknown item type: %r', i_type)
        return None

    def table(self, media):
        if type(media) is not str:
            media = self.media(media)

        if media == 'movies':
            return self.movies

        if media in ['shows', 'seasons', 'episodes']:
            return self.shows

        log.warn('Unknown media: %r', media)
        return None

    def __call__(self, media):
        return self.table(media)

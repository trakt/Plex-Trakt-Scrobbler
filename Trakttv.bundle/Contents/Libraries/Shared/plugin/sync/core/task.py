from plugin.core.database import Database
from plugin.core.helpers.variable import dict_path
from plugin.models import *
from plugin.sync.core.exception_logger import ExceptionLogger

from datetime import datetime
from peewee import JOIN_LEFT_OUTER
from plex import Plex
from plex_database.library import Library
from plex_database.matcher import Matcher
from stash import ApswArchive, Stash
from trakt import Trakt
from trakt_sync.cache.backends import StashBackend
from trakt_sync.cache.main import Cache
from trakt_sync.differ.core.base import KEY_AGENTS
import logging

GUID_AGENTS = [
    'imdb',
    'tvdb',

    'tmdb',
    'trakt',
    'tvrage'
]

log = logging.getLogger(__name__)


class SyncTask(object):
    def __init__(self, account, mode, data, media, result, status, **kwargs):
        self.account = account

        # Sync options
        self.mode = mode
        self.data = data
        self.media = media

        # Extra arguments
        self.kwargs = kwargs

        # Global syncing information
        self.artifacts = SyncArtifacts(self)
        self.progress = SyncProgress(self)
        self.state = SyncState(self)

        # State/Result management
        self.result = result
        self.status = status

        self.exceptions = []

        self.started = False
        self.success = None

    @property
    def elapsed(self):
        if self.result is None:
            return None

        return (datetime.utcnow() - self.result.started_at).total_seconds()

    def finish(self):
        # Update result in database
        self.result.ended_at = datetime.utcnow()
        self.result.success = self.success
        self.result.save()

        # Store exceptions in database
        for exc_info in self.exceptions:
            try:
                ExceptionLogger.result_store(self.result, exc_info)
            except Exception, ex:
                log.warn('Unable to store exception: %s', str(ex), exc_info=True)

        # Flush caches to archives
        self.state.flush()

    @classmethod
    def create(cls, account, mode, data, media, **kwargs):
        # Get account
        if type(account) is int:
            # TODO Move account retrieval/join to `Account` class
            account = (Account
                .select(
                    Account.id,
                    Account.name,

                    PlexAccount.id,
                    PlexAccount.username,
                    PlexBasicCredential.token,

                    TraktAccount.username,
                    TraktBasicCredential.token,

                    TraktOAuthCredential.access_token,
                    TraktOAuthCredential.refresh_token,
                    TraktOAuthCredential.created_at,
                    TraktOAuthCredential.expires_in
                )
                # Plex
                .join(
                    PlexAccount, JOIN_LEFT_OUTER, on=(
                        PlexAccount.account == Account.id
                    ).alias('plex')
                )
                .join(
                    PlexBasicCredential, JOIN_LEFT_OUTER, on=(
                        PlexBasicCredential.account == PlexAccount.id
                    ).alias('basic')
                )
                # Trakt
                .switch(Account)
                .join(
                    TraktAccount, JOIN_LEFT_OUTER, on=(
                        TraktAccount.account == Account.id
                    ).alias('trakt')
                )
                .join(
                    TraktBasicCredential, JOIN_LEFT_OUTER, on=(
                        TraktBasicCredential.account == TraktAccount.id
                    ).alias('basic')
                )
                .switch(TraktAccount)
                .join(
                    TraktOAuthCredential, JOIN_LEFT_OUTER, on=(
                        TraktOAuthCredential.account == TraktAccount.id
                    ).alias('oauth')
                )
                .where(Account.id == account)
                .get()
            )
        elif type(account) is not Account:
            raise ValueError('Unexpected value provided for the "account" parameter')

        # Get/Create sync status
        status = SyncStatus.get_or_create(
            account=account,
            mode=mode
        )

        # Create new sync result object
        result = SyncResult.create(
            status=status,
            started_at=datetime.utcnow()
        )

        return SyncTask(
            account, mode,
            data, media,
            result, status,
            **kwargs
        )


class SyncState(object):
    def __init__(self, task):
        self.task = task

        self.plex = SyncStatePlex(self)
        self.trakt = SyncStateTrakt(self)

    def flush(self):
        self.trakt.flush()


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

    def refresh(self):
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

        log.debug('Built table with %d keys', len(self.table))

    def flush(self):
        self.cache.collections.flush()

        for store in self.cache.stores.values():
            store.flush()


class SyncProgress(object):
    speed_smoothing = 0.75

    def __init__(self, task):
        self.task = task

        self._current = None
        self._maximum = None

        self._started_at = None
        self._ended_at = None

        self._speed = None

    @property
    def elapsed(self):
        if self._started_at and self._ended_at:
            return (self._ended_at - self._started_at).total_seconds()

        if self._started_at:
            return (datetime.utcnow() - self._started_at).total_seconds()

        return None

    @property
    def per_second(self):
        elapsed = self.elapsed

        if not elapsed:
            return None

        return float(self._current) / elapsed

    @property
    def percent(self):
        if self._maximum is None or self._current is None:
            return None

        return (float(self._current) / self._maximum) * 100

    @property
    def remaining(self):
        if self._maximum is None or self._current is None:
            return None

        return self._maximum - self._current

    @property
    def remaining_seconds(self):
        remaining = self.remaining

        if remaining is None or self._speed is None:
            return None

        return float(remaining) / self._speed

    def start(self, maximum):
        self._current = 0
        self._maximum = maximum

        self._started_at = datetime.utcnow()
        self._ended_at = None

        self._speed = None

    def step(self, delta=1):
        if self._current is None:
            self._current = 0

        self._current += delta

        # Update average syncing speed
        self.update_speed()

    def update_speed(self):
        if self._speed is None:
            # First sample, set to current `per_second`
            self._speed = self.per_second
            return

        # Calculate average syncing speed (EMA)
        self._speed = self.speed_smoothing * self.per_second + (1 - self.speed_smoothing) * self._speed

    def stop(self):
        self._ended_at = datetime.utcnow()


class SyncArtifacts(object):
    def __init__(self, task):
        self.task = task

        self.artifacts = {}

    def flatten(self):
        for data, actions in self.artifacts.items():
            for action, request in actions.items():
                if 'shows' in request:
                    request['shows'] = list(self.flatten_shows(request['shows']))

                if 'movies' in request:
                    request['movies'] = request['movies'].values()

                yield data, action, request

    @staticmethod
    def flatten_shows(shows):
        for show in shows.itervalues():
            if 'seasons' not in show:
                yield show
                continue

            show['seasons'] = show['seasons'].values()

            for season in show['seasons']:
                if 'episodes' not in season:
                    continue

                season['episodes'] = season['episodes'].values()

            yield show

    def send(self):
        for data, action, request in self.flatten():
            self.send_action(data, action, **request)

    @staticmethod
    def send_action(data, action, **kwargs):
        # Ensure items exist in `kwargs`
        if not kwargs:
            return False

        if not kwargs.get('movies') and not kwargs.get('shows'):
            return False

        # Try retrieve interface for `data`
        interface = Cache.Data.get_interface(data)

        if interface == 'sync/watched':
            # Watched add/remove functions are on the "sync/history" interface
            interface = 'sync/history'

        if interface is None:
            log.warn('[%s](%s) Unknown data type', data, action)
            return False

        # Try retrieve method for `action`
        func = getattr(Trakt[interface], action, None)

        if func is None:
            log.warn('[%s](%s) Unable find action in interface', data, action)
            return False

        # Send request to trakt.tv
        response = func(kwargs)

        if response is None:
            return False

        log.debug('[%s](%s) Response: %r', data, action, response)
        return True

    def store_episode(self, data, action, p_guid, identifier, p_show, **kwargs):
        key = (p_guid.agent, p_guid.sid)
        season_num, episode_num = identifier

        shows = dict_path(self.artifacts, [
            data,
            action,
            'shows'
        ])

        # Build show
        if key in shows:
            show = shows[key]
        else:
            show = self._build_request(p_guid, p_show)

            if show is None:
                return False

            # Store `show` in artifacts
            show['seasons'] = {}

            shows[key] = show

        # Build season
        if season_num in show['seasons']:
            season = show['seasons'][season_num]
        else:
            season = show['seasons'][season_num] = {'number': season_num}
            season['episodes'] = {}

        # Build episode
        if episode_num in season['episodes']:
            episode = season['episodes'][episode_num]
        else:
            episode = season['episodes'][episode_num] = {'number': episode_num}

        # Set `kwargs` on `episode`
        self._set_kwargs(episode, kwargs)
        return True

    def store_movie(self, data, action, p_guid, p_movie, **kwargs):
        key = (p_guid.agent, p_guid.sid)

        movies = dict_path(self.artifacts, [
            data,
            action,
            'movies'
        ])

        # Build movie
        if key in movies:
            movie = movies[key]
        else:
            movie = self._build_request(p_guid, p_movie, **kwargs)

            if movie is None:
                return False

            # Store `movie` in artifacts
            movies[key] = movie

        # Set `kwargs` on `movie`
        self._set_kwargs(movie, kwargs)
        return True

    @classmethod
    def _build_request(cls, p_guid, p_item, **kwargs):
        # Validate parameters
        if not p_item.get('title') or not p_item.get('year'):
            log.warn('Invalid "title" or "year" attribute on <%r (%r)>', p_item.get('title'), p_item.get('year'))
            return None

        if not p_guid:
            log.warn('Invalid GUID attribute on <%r (%r)>', p_item.get('title'), p_item.get('year'))
            return None

        if p_guid.agent not in GUID_AGENTS:
            log.warn('GUID agent %r is not supported on <%r (%r)>', p_guid.agent, p_item.get('title'), p_item.get('year'))
            return None

        # Build request
        request = {
            'title': p_item['title'],
            'year': p_item['year'],

            'ids': {}
        }

        # Set identifier
        request['ids'][p_guid.agent] = p_guid.sid

        # Set extra attributes
        cls._set_kwargs(request, kwargs)

        return request

    @staticmethod
    def _set_kwargs(request, kwargs):
        for key, value in kwargs.items():
            if type(value) is datetime:
                try:
                    # Convert `datetime` object to string
                    value = value.strftime('%Y-%m-%dT%H:%M:%S') + '.000-00:00'
                except Exception, ex:
                    log.warn('Unable to convert %r to string', value)
                    return False

            request[key] = value

        return True

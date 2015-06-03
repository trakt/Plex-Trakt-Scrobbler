from plugin.core.database import Database
from plugin.models import *
from plugin.sync.core.exception_logger import ExceptionLogger

from datetime import datetime
from peewee import JOIN_LEFT_OUTER
from plex import Plex
from plex_database.library import Library
from plex_database.matcher import Matcher
from stash import ApswArchive, Stash
from trakt_sync.cache.backends import StashBackend
from trakt_sync.cache.main import Cache
from trakt_sync.differ.core.base import KEY_AGENTS
import logging

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
        self.progress = SyncProgress(self)
        self.state = SyncState(self)

        # State/Result management
        self.result = result
        self.status = status

        self.exceptions = []
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

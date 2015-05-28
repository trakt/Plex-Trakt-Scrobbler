from plugin.core.database import Database
from plugin.models import *

from peewee import JOIN_LEFT_OUTER
from plex import Plex
from plex_database.library import Library
from plex_database.matcher import Matcher
from stash import ApswArchive, Stash
from trakt_sync.cache.backends import StashBackend
from trakt_sync.cache.main import Cache
import logging
from trakt_sync.differ.core.base import KEY_AGENTS

log = logging.getLogger(__name__)


class SyncTask(object):
    def __init__(self, account, mode, data, media, **kwargs):
        self.account = account

        self.mode = mode

        self.data = data
        self.media = media

        self.kwargs = kwargs

        self.state = SyncState(self)

    @classmethod
    def create(cls, account, mode, data, media, **kwargs):
        log.debug(type(account))

        if type(account) is int:
            account = (Account
                .select(
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

        return SyncTask(
            account, mode,
            data, media,
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

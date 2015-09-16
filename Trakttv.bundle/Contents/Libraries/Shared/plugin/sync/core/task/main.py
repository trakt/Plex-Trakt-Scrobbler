from plugin.managers import ExceptionManager
from plugin.models import *
from plugin.sync.core.enums import SyncData, SyncMode
from plugin.sync.core.exceptions import SyncAbort
from plugin.sync.core.task.artifacts import SyncArtifacts
from plugin.sync.core.task.configuration import SyncConfiguration
from plugin.sync.core.task.progress import SyncProgress
from plugin.sync.core.task.profiler import SyncProfiler
from plugin.sync.core.task.state import SyncState

from datetime import datetime
from peewee import JOIN_LEFT_OUTER
import logging
import time

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

        # State/Result management
        self.result = result
        self.status = status

        self.exceptions = []

        self.finished = False
        self.started = False
        self.success = None

        self._abort = False

        # Construct children
        self.artifacts = SyncArtifacts(self)
        self.configuration = SyncConfiguration(self)
        self.progress = SyncProgress(self)
        self.profiler = SyncProfiler(self)

        self.state = SyncState(self)

    @property
    def id(self):
        if self.result is None:
            return None

        return self.result.id

    @property
    def elapsed(self):
        if self.result is None:
            return None

        return (datetime.utcnow() - self.result.started_at).total_seconds()

    def load(self):
        # Load task configuration
        self.configuration.load(self.account)

        # Automatically determine enabled data types
        if self.data is None:
            self.data = self.get_enabled_data(self.configuration, self.mode)

        log.debug('Sync Data: %r', self.data)
        log.debug('Sync Media: %r', self.media)

        # Load children
        self.profiler.load()
        self.state.load()

    def abort(self, timeout=None):
        # Set `abort` flag, thread will abort on the next `checkpoint()`
        self._abort = True

        if timeout is None:
            return

        # Wait `timeout` seconds for task to finish
        for x in xrange(timeout):
            if self.finished:
                return

            time.sleep(1)

    def checkpoint(self):
        # Check if an abort has been requested
        if not self._abort:
            return

        raise SyncAbort()

    def finish(self):
        # Update result in database
        self.result.ended_at = datetime.utcnow()
        self.result.success = self.success
        self.result.save()

        # Store exceptions in database
        for exc_info in self.exceptions:
            try:
                self.store_exception(self.result, exc_info)
            except Exception, ex:
                log.warn('Unable to store exception: %s', str(ex), exc_info=True)

        # Flush caches to archives
        self.state.flush()

        # Display profiler report
        self.profiler.log_report()

        # Mark finished
        self.finished = True

    @staticmethod
    def store_exception(result, exc_info):
        exception, error = ExceptionManager.create.from_exc_info(exc_info)

        # Link error to result
        SyncResultError.create(
            result=result,
            error=error
        )

        # Link exception to result
        SyncResultException.create(
            result=result,
            exception=exception
        )

    @classmethod
    def create(cls, account, mode, data, media, trigger, **kwargs):
        # Get account
        if type(account) is int:
            account = cls.get_account(account)
        elif type(account) is not Account:
            raise ValueError('Unexpected value provided for the "account" parameter')

        # Get/Create sync status
        status, created = SyncStatus.get_or_create(
            account=account,
            mode=mode
        )

        # Create sync result
        result = SyncResult.create(
            status=status,
            trigger=trigger,

            started_at=datetime.utcnow()
        )

        # Create sync task
        task = SyncTask(
            account, mode,
            data, media,
            result, status,
            **kwargs
        )

        # Load sync configuration/state
        task.load()

        return task

    @classmethod
    def get_account(cls, account_id):
        # TODO Move account retrieval/join to `Account` class
        return (
            Account.select(
                Account.id,
                Account.name,

                PlexAccount.id,
                PlexAccount.key,
                PlexAccount.username,
                PlexBasicCredential.token_plex,
                PlexBasicCredential.token_server,

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
            .where(Account.id == account_id)
            .get()
        )

    @classmethod
    def get_enabled_data(cls, configuration, mode):
        enabled = []

        # Determine accepted modes
        modes = [SyncMode.Full, mode]

        if mode == SyncMode.FastPull:
            modes.append(SyncMode.Pull)

        # Retrieve enabled data
        if configuration['sync.watched.mode'] in modes:
            enabled.append(SyncData.Watched)

        if configuration['sync.ratings.mode'] in modes:
            enabled.append(SyncData.Ratings)

        if configuration['sync.playback.mode'] in modes:
            enabled.append(SyncData.Playback)

        if configuration['sync.collection.mode'] in modes:
            enabled.append(SyncData.Collection)

        if configuration['sync.watchlist.mode'] == mode:
            enabled.append(SyncData.Watchlist)

        # Convert to enum value
        result = None

        for data in enabled:
            if result is None:
                result = data
                continue

            result |= data

        return result

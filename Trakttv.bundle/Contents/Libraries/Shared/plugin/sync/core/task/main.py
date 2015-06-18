from plugin.managers import ExceptionManager
from plugin.models import *
from plugin.sync.core.task.artifacts import SyncArtifacts
from plugin.sync.core.task.configuration import SyncConfiguration
from plugin.sync.core.task.progress import SyncProgress
from plugin.sync.core.task.state.main import SyncState

from datetime import datetime
from peewee import JOIN_LEFT_OUTER
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
        self.artifacts = SyncArtifacts(self)
        self.configuration = SyncConfiguration(self)
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
                self.store_exception(self.result, exc_info)
            except Exception, ex:
                log.warn('Unable to store exception: %s', str(ex), exc_info=True)

        # Flush caches to archives
        self.state.flush()

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

        # Create sync result
        result = SyncResult.create(
            status=status,
            started_at=datetime.utcnow()
        )

        # Create sync task
        task = SyncTask(
            account, mode,
            data, media,
            result, status,
            **kwargs
        )

        # Load configuration options from database
        task.configuration.load(account)

        return task

from plugin.models.core import db
from plugin.models.m_sync.status import SyncStatus
from plugin.models.exception import Exception
from plugin.models.message import Message

from exception_wrappers.libraries.playhouse.apsw_ext import *


class SyncResultTrigger(object):
    Manual          = 0x00

    LibraryUpdate   = 0x01
    Schedule        = 0x02


class SyncResult(Model):
    Trigger = SyncResultTrigger

    class Meta:
        database = db
        db_table = 'sync.result'

    status = ForeignKeyField(SyncStatus, 'history')

    trigger = IntegerField(default=SyncResultTrigger.Manual)

    # Timestamps
    started_at = DateTimeField(null=True)
    ended_at = DateTimeField(null=True)

    # Result
    success = BooleanField(null=True)

    def get_errors(self):
        query = (SyncResultError
            .select(SyncResultError, Message)
            .join(Message, JOIN_LEFT_OUTER, on=(
                Message.id == SyncResultError.error
            ).alias('message'))
            .where(
                SyncResultError.result == self
            )
        )

        return [
            item.message
            for item in query
        ]

    @classmethod
    def get_latest(cls, account, mode, section=None):
        return (SyncStatus
                .select(SyncStatus, SyncResult)
                .join(SyncResult, JOIN_LEFT_OUTER, on=(
                    SyncResult.status == SyncStatus.id
                ).alias('latest'))
                .where(
                    SyncStatus.account == account,
                    SyncStatus.mode == mode,
                    SyncStatus.section == section,

                    SyncResult.success != None
                )
                .order_by(SyncResult.started_at.desc())
                .limit(1)
        )


class SyncResultError(Model):
    class Meta:
        database = db
        db_table = 'sync.result.error'

    result = ForeignKeyField(SyncResult, 'errors')
    error = ForeignKeyField(Message, 'results')


class SyncResultException(Model):
    class Meta:
        database = db
        db_table = 'sync.result.exception'

    result = ForeignKeyField(SyncResult, 'exceptions')
    exception = ForeignKeyField(Exception, 'results')

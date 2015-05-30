from plugin.models.core import db
from plugin.models.m_sync.status import SyncStatus
from plugin.models.exception import Exception
from plugin.models.message import Message

from playhouse.apsw_ext import *


class SyncResult(Model):
    class Meta:
        database = db
        db_table = 'sync.result'

    status = ForeignKeyField(SyncStatus, 'history')

    # Timestamps
    started_at = DateTimeField(null=True)
    ended_at = DateTimeField(null=True)

    # Result
    success = BooleanField(null=True)


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

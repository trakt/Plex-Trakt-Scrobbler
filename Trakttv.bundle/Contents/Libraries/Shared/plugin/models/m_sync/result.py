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

    timestamp = DateTimeField()
    success = BooleanField()

    # Failure details
    error = ForeignKeyField(Message, null=True)
    exception = ForeignKeyField(Exception, null=True)

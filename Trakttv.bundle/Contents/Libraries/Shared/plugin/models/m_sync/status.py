from plugin.models.core import db
from plugin.models.account import Account

from exception_wrappers.libraries.playhouse.apsw_ext import *


class SyncStatus(Model):
    class Meta:
        database = db
        db_table = 'sync.status'

    account = ForeignKeyField(Account, 'sync_status')

    mode = IntegerField()
    section = CharField(null=True, max_length=3)

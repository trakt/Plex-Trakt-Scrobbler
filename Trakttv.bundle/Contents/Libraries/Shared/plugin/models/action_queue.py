from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.session import Session

from exception_wrappers.libraries.playhouse.apsw_ext import *


class ActionQueue(Model):
    class Meta:
        database = db
        db_table = 'action.queue'
        primary_key = CompositeKey('session', 'event')

    account = ForeignKeyField(Account, 'action_queue')
    session = ForeignKeyField(Session, 'action_queue', null=True)

    progress = FloatField(null=True)

    part = IntegerField(default=1)
    rating_key = IntegerField(null=True)

    event = CharField()
    request = BlobField()

    queued_at = DateTimeField()

    @property
    def account_id(self):
        return self._data['account']

    @property
    def session_id(self):
        return self._data['session']

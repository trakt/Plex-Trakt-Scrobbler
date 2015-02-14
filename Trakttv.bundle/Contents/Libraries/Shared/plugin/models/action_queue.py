from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.session import Session

from peewee import *


class ActionQueue(Model):
    class Meta:
        database = db
        primary_key = CompositeKey('session', 'event')

    account = ForeignKeyField(Account, 'action_queue')
    session = ForeignKeyField(Session, 'action_queue', null=True)

    event = CharField()
    request = BlobField()

    queued_at = DateTimeField()

    @property
    def account_id(self):
        return self._data['account']

    @property
    def session_id(self):
        return self._data['session']

from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.session import Session

from playhouse.apsw_ext import *


class ActionHistory(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'action_history')
    session = ForeignKeyField(Session, 'action_history', null=True)

    event = CharField()
    performed = CharField(null=True)

    queued_at = DateTimeField()
    sent_at = DateTimeField()

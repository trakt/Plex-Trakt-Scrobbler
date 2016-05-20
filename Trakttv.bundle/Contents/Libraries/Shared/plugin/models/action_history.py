from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.session import Session

from playhouse.apsw_ext import *


class ActionHistory(Model):
    class Meta:
        database = db
        db_table = 'action.history'

    account = ForeignKeyField(Account, 'action_history')
    session = ForeignKeyField(Session, 'action_history', null=True)

    rating_key = IntegerField(null=True)

    event = CharField()
    performed = CharField(null=True)

    queued_at = DateTimeField()
    sent_at = DateTimeField()

    @classmethod
    def has_scrobbled(cls, account, rating_key, after):
        # Find matching "scrobble" events
        results = ActionHistory.select().where(
            ActionHistory.account == account,
            ActionHistory.rating_key == rating_key,

            ActionHistory.performed == 'scrobble',

            ActionHistory.sent_at > after
        )

        # Check for at least one result
        return results.count() > 0

from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.session import Session

from exception_wrappers.libraries.playhouse.apsw_ext import *


class ActionHistory(Model):
    class Meta:
        database = db
        db_table = 'action.history'

    account = ForeignKeyField(Account, 'action_history')
    session = ForeignKeyField(Session, 'action_history', null=True)

    part = IntegerField(default=1)
    rating_key = IntegerField(null=True)

    event = CharField()
    performed = CharField(null=True)

    queued_at = DateTimeField()
    sent_at = DateTimeField()

    @classmethod
    def has_scrobbled(cls, account, rating_key, after, part=None):
        where = [
            ActionHistory.account == account,
            ActionHistory.rating_key == rating_key,

            ActionHistory.performed == 'scrobble',

            ActionHistory.sent_at > after
        ]

        if part is not None:
            where.append(ActionHistory.part == part)

        # Find matching "scrobble" events
        results = ActionHistory.select().where(*where)

        # Check for at least one result
        return results.count() > 0

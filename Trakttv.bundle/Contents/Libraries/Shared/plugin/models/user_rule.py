from plugin.models import Account
from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


class UserRule(Model):
    class Meta:
        database = db
        db_table = 'session.user.rule'

    account = ForeignKeyField(Account, 'user_rules', null=True)
    account_function = CharField(null=True)

    name = CharField(null=True)

    priority = IntegerField()

    @property
    def account_id(self):
        try:
            return self._data['account']
        except KeyError:
            return None

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'priority': self.priority,

            'name': self.name
        }

        if not full:
            return result

        # Update `result` with account details
        if self.account_id:
            result['account'] = self.account.to_json()
        else:
            result['account_function'] = self.account_function

        return result

    def __repr__(self):
        return '<UserRule priority: %r, account: %s, name: %r>' % (
            self.priority,
            repr(self.account_id) if self.account_id else self.account_function,
            self.name
        )

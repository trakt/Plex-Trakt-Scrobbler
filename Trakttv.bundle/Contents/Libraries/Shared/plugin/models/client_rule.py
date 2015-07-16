from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class ClientRule(Model):
    class Meta:
        database = db
        db_table = 'session.client.rule'

    account = ForeignKeyField(Account, 'client_rules', null=True)
    account_function = CharField(null=True)

    key = CharField(null=True)
    name = CharField(null=True)
    address = CharField(null=True)

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

            'key': self.key,
            'name': self.name,
            'address': self.address
        }

        if full and self.account_id:
            result['account'] = self.account.to_json()

        return result

    def __repr__(self):
        return '<ClientRule priority: %r, account: %s, key: %r, name: %r, address: %r>' % (
            self.priority,
            repr(self.account_id) if self.account_id else self.account_function,
            self.key,
            self.name,
            self.address
        )

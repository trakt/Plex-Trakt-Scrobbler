from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class ClientRule(Model):
    class Meta:
        database = db
        db_table = 'session.client.rule'

    account = ForeignKeyField(Account, 'client_rules')

    key = CharField(null=True)
    name = CharField(null=True)
    address = CharField(null=True)

    priority = IntegerField()

    @property
    def account_id(self):
        return self._data['account']

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'priority': self.priority,

            'key': self.key,
            'name': self.name,
            'address': self.address
        }

        if full:
            result['account'] = self.account.to_json()

        return result

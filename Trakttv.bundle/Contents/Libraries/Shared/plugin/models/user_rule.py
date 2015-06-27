from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class UserRule(Model):
    class Meta:
        database = db
        db_table = 'session.user.rule'

    account = ForeignKeyField(Account, 'user_rules')

    name = CharField(null=True)

    priority = IntegerField()

    @property
    def account_id(self):
        return self._data['account']

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'priority': self.priority,

            'name': self.name
        }

        if full:
            result['account'] = self.account.to_json()

        return result

from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class UserRule(Model):
    class Meta:
        database = db
        primary_key = CompositeKey('name')

    account = ForeignKeyField(Account, 'user_rules')

    name = CharField(null=True)

    @property
    def account_id(self):
        return self._data['account']

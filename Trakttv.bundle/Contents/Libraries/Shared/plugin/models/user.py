from plugin.models import Account
from plugin.models.core import db

from peewee import *


class User(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'users', null=True)

    id = IntegerField(unique=True)
    name = CharField(null=True)

    thumb = CharField(null=True)

    @property
    def account_id(self):
        return self._data.get('account')

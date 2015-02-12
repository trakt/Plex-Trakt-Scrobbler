from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.client import Client
from plugin.models.user import User

from peewee import *


class Session(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'sessions')
    client = ForeignKeyField(Client, 'sessions', to_field='machine_identifier', null=True)
    user = ForeignKeyField(User, 'sessions', to_field='id', null=True)

    rating_key = IntegerField(null=True)
    session_key = IntegerField(null=True, unique=True)

    state = CharField(null=True)
    view_offset = IntegerField(null=True)

    @property
    def account_id(self):
        return self._data['account']

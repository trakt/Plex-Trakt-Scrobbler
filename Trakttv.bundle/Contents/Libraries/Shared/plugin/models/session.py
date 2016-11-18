from plugin.models.core import db
from plugin.models.account import Account
from plugin.models.client import Client
from plugin.models.user import User

from exception_wrappers.libraries.playhouse.apsw_ext import *


class Session(Model):
    class Meta:
        database = db

    account = ForeignKeyField(Account, 'sessions', null=True)
    client = ForeignKeyField(Client, 'sessions', to_field='key', null=True)
    user = ForeignKeyField(User, 'sessions', to_field='key', null=True)

    rating_key = IntegerField(null=True)
    session_key = TextField(null=True, unique=True)

    state = CharField(null=True)

    part = IntegerField(default=1)
    part_count = IntegerField(default=1)
    part_duration = IntegerField(null=True)

    duration = IntegerField(null=True)
    view_offset = IntegerField(null=True)
    progress = FloatField(null=True)

    updated_at = DateTimeField(null=True)

    @property
    def account_id(self):
        return self._data.get('account')

    @property
    def payload(self):
        return {
            'part': self.part,
            'rating_key': self.rating_key,
            'view_offset': self.view_offset
        }

    def __repr__(self):
        return '<Session session_key: %r, state: %r>' % (
            self.session_key,
            self.state
        )

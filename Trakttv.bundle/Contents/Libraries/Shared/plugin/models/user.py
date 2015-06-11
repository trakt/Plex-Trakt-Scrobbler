from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class User(Model):
    class Meta:
        database = db
        db_table = 'session.user'

    account = ForeignKeyField(Account, 'users', null=True)

    # Identification
    key = IntegerField(unique=True)
    name = CharField(null=True)

    thumb = CharField(null=True)

    @property
    def account_id(self):
        return self._data.get('account')

    def __repr__(self):
        return '<User id: %r, key: %r>' % (self.id, self.key)

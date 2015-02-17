from plugin.models.core import db

from playhouse.apsw_ext import *


class Account(Model):
    class Meta:
        database = db

    username = CharField(unique=True)
    password = CharField()

    token = CharField(null=True)

    @property
    def authenticated(self):
        return self.token is not None

    def __repr__(self):
        return '<Account username: %r, authenticated: %r>' % (
            self.username,
            self.authenticated
        )

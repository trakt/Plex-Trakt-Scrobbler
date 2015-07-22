from plugin.models.m_plex.account import PlexAccount
from plugin.models.core import db

from playhouse.apsw_ext import *


class PlexBasicCredential(Model):
    class Meta:
        database = db
        db_table = 'plex.credential.basic'

    account = ForeignKeyField(PlexAccount, 'basic_credentials', unique=True)

    password = CharField(null=True)

    # Authorization
    token = CharField(null=True)

    @property
    def state(self):
        if self.token is not None:
            return 'valid'

        if self.password is not None:
            return 'warning'

        return 'empty'

    def to_json(self, account):
        result = {
            'state': self.state,

            'username': account.username
        }

        if self.password:
            result['password'] = '*' * len(self.password)
        elif self.token:
            result['password'] = '*' * 8

        return result

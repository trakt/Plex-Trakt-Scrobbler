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

    def to_json(self, account):
        result = {
            'valid': self.token is not None,

            'username': account.username
        }

        if self.password:
            result['password'] = '*' * len(self.password)
        elif self.token:
            result['password'] = '*' * 8

        return result

from plugin.models.m_trakt.account import TraktAccount
from plugin.models.core import db

from playhouse.apsw_ext import *


class TraktBasicCredential(Model):
    class Meta:
        database = db
        db_table = 'trakt.credential.basic'

    account = ForeignKeyField(TraktAccount, 'basic_credentials', unique=True)

    password = CharField(null=True)

    # Authorization
    token = CharField(null=True)


class TraktOAuthCredential(Model):
    class Meta:
        database = db
        db_table = 'trakt.credential.oauth'

    account = ForeignKeyField(TraktAccount, 'oauth_credentials', unique=True)

    code = CharField(null=True)

    # Authorization
    access_token = CharField()
    refresh_token = CharField()

    created_at = IntegerField()
    expires_in = IntegerField()

    token_type = CharField()
    scope = CharField()

    def to_response(self):
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,

            'created_at': self.created_at,
            'expires_in': self.expires_in,

            'token_type': self.token_type,
            'scope': self.scope
        }

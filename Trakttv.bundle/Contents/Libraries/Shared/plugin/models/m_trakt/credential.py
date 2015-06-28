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


class TraktOAuthCredential(Model):
    class Meta:
        database = db
        db_table = 'trakt.credential.oauth'

    account = ForeignKeyField(TraktAccount, 'oauth_credentials', unique=True)

    code = CharField(null=True)

    # Authorization
    access_token = CharField(null=True)
    refresh_token = CharField(null=True)

    created_at = IntegerField(null=True)
    expires_in = IntegerField(null=True)

    token_type = CharField(null=True)
    scope = CharField(null=True)

    def is_valid(self):
        return self.access_token is not None

    def to_json(self):
        result = {
            'valid': self.access_token is not None
        }

        if self.code:
            result['code'] = '*' * len(self.code)

        return result

    def to_response(self):
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,

            'created_at': self.created_at,
            'expires_in': self.expires_in,

            'token_type': self.token_type,
            'scope': self.scope
        }

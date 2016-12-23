from plugin.models.m_trakt.account import TraktAccount
from plugin.models.core import db

from exception_wrappers.libraries.playhouse.apsw_ext import *


class TraktBasicCredential(Model):
    class Meta:
        database = db
        db_table = 'trakt.credential.basic'

    account = ForeignKeyField(TraktAccount, 'basic_credentials', unique=True)

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

    def is_valid(self):
        return self.token is not None

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

    @property
    def state(self):
        if self.is_valid():
            return 'valid'

        if self.code is not None:
            return 'warning'

        return 'empty'

    def is_valid(self):
        # TODO check token hasn't expired
        return self.access_token is not None

    def to_json(self):
        result = {
            'state': self.state
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

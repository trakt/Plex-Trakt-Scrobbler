from plugin.models import Account
from plugin.models.core import db

from playhouse.apsw_ext import *


class Credential(Model):
    class Meta:
        database = db


class BasicCredential(Credential):
    account = ForeignKeyField(Account, 'basic_credentials', unique=True)

    password = CharField(null=True)

    # Authorization
    token = CharField(null=True)


class OAuthCredential(Credential):
    account = ForeignKeyField(Account, 'oauth_credentials', unique=True)

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

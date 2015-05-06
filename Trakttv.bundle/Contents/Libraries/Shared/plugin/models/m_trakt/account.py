from plugin.models.core import db
from plugin.models.account import Account

from playhouse.apsw_ext import *
from trakt import Trakt
import logging

log = logging.getLogger(__name__)


class TraktAccount(Model):
    class Meta:
        database = db
        db_table = 'trakt.account'

    account = ForeignKeyField(Account, 'trakt_accounts', unique=True)

    username = CharField(null=True, unique=True)

    def authorization(self):
        # OAuth
        oauth = self.oauth_credentials.first()

        if oauth:
            return self.oauth_authorization(oauth)

        # Basic (legacy)
        basic = self.basic_credentials.first()

        if basic:
            return self.basic_authorization(basic)

        # No account authorization available
        raise Exception("Account hasn't been authenticated")

    def basic_authorization(self, basic_credential=None):
        if basic_credential is None:
            basic_credential = self.basic_credentials.first()

        log.debug('Using basic authorization for %r', self)

        return Trakt.configuration.auth(self.username, basic_credential.token)

    def oauth_authorization(self, oauth_credential=None):
        if oauth_credential is None:
            oauth_credential = self.oauth_credentials.first()

        log.debug('Using oauth authorization for %r', self)

        return Trakt.configuration.oauth.from_response(oauth_credential.to_response(), refresh=True)

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'username': self.username
        }

        if not full:
            return result

        # Merge authorization details
        result['authorization'] = {
            'basic': {'valid': False},
            'oauth': {'valid': False}
        }

        # - Basic credentials
        basic = self.basic_credentials.first()

        if basic is not None:
            result['authorization']['basic'] = basic.to_json(self)

        # - OAuth credentials
        oauth = self.oauth_credentials.first()

        if oauth is not None:
            result['authorization']['oauth'] = oauth.to_json()

        return result

    def __repr__(self):
        return '<Account username: %r>' % (
            self.username,
        )

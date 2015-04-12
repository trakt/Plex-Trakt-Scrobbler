from plugin.models.core import db

from playhouse.apsw_ext import *
from trakt import Trakt
import logging

log = logging.getLogger(__name__)


class Account(Model):
    class Meta:
        database = db

    username = CharField(unique=True)

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

    def __repr__(self):
        return '<Account username: %r>' % (
            self.username,
        )

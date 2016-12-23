from plugin.core.exceptions import AccountAuthenticationError
from plugin.models.core import db
from plugin.models.account import Account

from datetime import datetime, timedelta
from exception_wrappers.libraries.playhouse.apsw_ext import *
from trakt import Trakt
from urllib import urlencode
from urlparse import urlparse, parse_qsl
import logging

REFRESH_INTERVAL = timedelta(days=1)

log = logging.getLogger(__name__)


class TraktAccount(Model):
    class Meta:
        database = db
        db_table = 'trakt.account'

    account = ForeignKeyField(Account, 'trakt_accounts', unique=True)

    username = CharField(null=True, unique=True)
    thumb = TextField(null=True)

    cover = TextField(null=True)
    timezone = TextField(null=True)

    refreshed_at = DateTimeField(null=True)

    def __init__(self, *args, **kwargs):
        super(TraktAccount, self).__init__(*args, **kwargs)

        self._basic_credential = None
        self._oauth_credential = None

    @property
    def basic(self):
        if self._basic_credential:
            return self._basic_credential

        return self.basic_credentials.first()

    @basic.setter
    def basic(self, value):
        self._basic_credential = value

    @property
    def oauth(self):
        if self._oauth_credential:
            return self._oauth_credential

        return self.oauth_credentials.first()

    @oauth.setter
    def oauth(self, value):
        self._oauth_credential = value

    def authorization(self):
        # OAuth
        oauth = self.oauth

        if oauth and oauth.is_valid():
            return self.oauth_authorization(oauth)

        # Basic (legacy)
        basic = self.basic

        if basic and basic.is_valid():
            return self.basic_authorization(basic)

        # No account authorization available
        raise AccountAuthenticationError("Trakt account hasn't been authenticated")

    def basic_authorization(self, basic_credential=None):
        if basic_credential is None:
            basic_credential = self.basic

        log.debug('Using basic authorization for %r', self)

        return Trakt.configuration.auth(self.username, basic_credential.token)

    def oauth_authorization(self, oauth_credential=None):
        if oauth_credential is None:
            oauth_credential = self.oauth

        log.debug('Using oauth authorization for %r', self)

        return Trakt.configuration.oauth.from_response(
            oauth_credential.to_response(),
            refresh=True,
            username=self.username
        )

    def refresh(self, force=False, save=True, settings=None):
        if not force and self.refreshed_at:
            # Only refresh account every `REFRESH_INTERVAL`
            since_refresh = datetime.utcnow() - self.refreshed_at

            if since_refresh < REFRESH_INTERVAL:
                return False

        if settings is None:
            # Fetch trakt account details
            with self.authorization().http(retry=force):
                settings = Trakt['users/settings'].get()

        # Update user details
        user = settings.get('user', {})
        avatar = user.get('images', {}).get('avatar', {})

        self.thumb = avatar.get('full')

        # Update account details
        account = settings.get('account', {})

        self.cover = account.get('cover_image')
        self.timezone = account.get('timezone')

        self.refreshed_at = datetime.utcnow()

        # Store changes in database
        if save:
            self.save()

        return True

    def thumb_url(self, default=None, rating='pg', size=256):
        if not self.thumb:
            return None

        thumb = urlparse(self.thumb)

        if not thumb.netloc.endswith('gravatar.com'):
            return None

        result = 'https://secure.gravatar.com%s' % thumb.path

        if default is None:
            query = dict(parse_qsl(thumb.query))

            default = query.get('d') or query.get('default')

        return result + '?' + urlencode({
            'd': default,
            'r': rating,
            's': size
        })

    def to_json(self, full=False):
        result = {
            'id': self.id,
            'username': self.username,

            'thumb_url': self.thumb_url()
        }

        if not full:
            return result

        # Merge authorization details
        result['authorization'] = {
            'basic': {'state': 'empty'},
            'oauth': {'state': 'empty'}
        }

        # - Basic credentials
        basic = self.basic

        if basic is not None:
            result['authorization']['basic'] = basic.to_json(self)

        # - OAuth credentials
        oauth = self.oauth

        if oauth is not None:
            result['authorization']['oauth'] = oauth.to_json()

        return result

    def __repr__(self):
        return '<TraktAccount username: %r>' % (
            self.username,
        )

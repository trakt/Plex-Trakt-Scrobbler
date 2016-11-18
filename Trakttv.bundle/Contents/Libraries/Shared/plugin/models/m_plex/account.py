from plugin.core.exceptions import AccountAuthenticationError
from plugin.models.core import db
from plugin.models.account import Account

from datetime import datetime, timedelta
from exception_wrappers.libraries.playhouse.apsw_ext import *
from plex import Plex
from urllib import urlencode
from urlparse import urlparse, parse_qsl
from xml.etree import ElementTree
import logging
import requests

REFRESH_INTERVAL = timedelta(days=1)

log = logging.getLogger(__name__)


class PlexAccount(Model):
    class Meta:
        database = db
        db_table = 'plex.account'

    account = ForeignKeyField(Account, 'plex_accounts', unique=True)

    key = IntegerField(null=True, unique=True)
    username = CharField(null=True, unique=True)

    title = CharField(null=True)
    thumb = TextField(null=True)

    refreshed_at = DateTimeField(null=True)

    def __init__(self, *args, **kwargs):
        super(PlexAccount, self).__init__(*args, **kwargs)

        self._basic_credential = None

    @property
    def account_id(self):
        return self._data.get('account')

    @property
    def basic(self):
        if self._basic_credential:
            return self._basic_credential

        return self.basic_credentials.first()

    @basic.setter
    def basic(self, value):
        self._basic_credential = value

    def authorization(self):
        # Basic
        basic = self.basic

        if basic:
            return self.basic_authorization(basic)

        # No account authorization available
        raise AccountAuthenticationError("Plex account hasn't been authenticated")

    def basic_authorization(self, basic_credential=None):
        if basic_credential is None:
            basic_credential = self.basic

        # Ensure token exists
        if basic_credential.token_server is None:
            raise AccountAuthenticationError("Plex account is missing the server token")

        # Handle anonymous authentication
        if basic_credential.token_server == 'anonymous':
            log.debug('Using anonymous authorization for %r', self)
            return Plex.configuration.authentication(token=None)

        # Configure client
        log.debug('Using basic authorization for %r', self)
        return Plex.configuration.authentication(basic_credential.token_server)

    def refresh(self, force=False, save=True):
        # Retrieve credentials
        basic = self.basic

        if not basic:
            return False

        # Check if refresh is required
        if self.refresh_required(basic):
            force = True

        # Only refresh account every `REFRESH_INTERVAL`
        if not force and self.refreshed_at:
            since_refresh = datetime.utcnow() - self.refreshed_at

            if since_refresh < REFRESH_INTERVAL:
                return False

        # Refresh account details
        if not self.refresh_details(basic):
            return False

        if not basic.refresh(force=True):
            return False

        # Store changes in database
        self.refreshed_at = datetime.utcnow()

        if save:
            self.save()

        return True

    def refresh_details(self, basic):
        if basic.token_plex == 'anonymous':
            return self.refresh_anonymous()

        log.info('Refreshing plex account: %r', self)

        # Fetch account details
        response = requests.get('https://plex.tv/users/account', headers={
            'X-Plex-Token': basic.token_plex
        })

        if not (200 <= response.status_code < 300):
            log.warn('Unable to retrieve account details from plex.tv (status_code: %s)', response.status_code)
            return False

        user = ElementTree.fromstring(response.content)

        # Update details
        self.username = user.attrib.get('username') or None

        self.title = user.attrib.get('title')
        self.thumb = user.attrib.get('thumb')

        # Update `key`
        if self.id == 1:
            # Use administrator `key`
            self.key = 1
        else:
            # Retrieve user id from plex.tv details
            try:
                user_id = int(user.attrib.get('id'))
            except Exception as ex:
                log.warn('Unable to cast user id to integer: %s', ex, exc_info=True)
                user_id = None

            # Update `key`
            self.key = user_id

        return True

    def refresh_anonymous(self):
        log.info('Refreshing plex account: %r (anonymous)', self)

        self.username = 'administrator'

        self.title = 'Administrator'
        self.thumb = None

        if self.id == 1:
            self.key = 1
        else:
            self.key = None

        return True

    def refresh_required(self, basic):
        if self.key is None:
            return True

        if self.title is None:
            return True

        if not basic.token_server:
            return True

        return False

    def thumb_url(self, default=None, rating='pg', size=256):
        if not self.thumb:
            return None

        thumb = urlparse(self.thumb)

        if thumb.netloc.endswith('plex.tv'):
            return self.thumb

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

            'title': self.title,
            'thumb_url': self.thumb_url()
        }

        if not full:
            return result

        # Merge authorization details
        result['authorization'] = {
            'basic': {'state': 'empty'}
        }

        # - Basic credentials
        basic = self.basic

        if basic is not None:
            result['authorization']['basic'] = basic.to_json(self)

        return result

    def __repr__(self):
        return '<PlexAccount username: %r>' % (
            self.username,
        )

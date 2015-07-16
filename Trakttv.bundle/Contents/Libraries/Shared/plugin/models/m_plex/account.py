from plugin.models.core import db
from plugin.models.account import Account

from datetime import datetime, timedelta
from playhouse.apsw_ext import *
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

    username = CharField(null=True, unique=True)
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

    def refresh(self, force=False, save=True):
        if not force and self.refreshed_at:
            # Only refresh account every `REFRESH_INTERVAL`
            since_refresh = datetime.utcnow() - self.refreshed_at

            if since_refresh < REFRESH_INTERVAL:
                return False

        # Fetch account details
        basic = self.basic

        if not basic:
            return False

        response = requests.get('https://plex.tv/users/account', headers={
            'X-Plex-Token': basic.token
        })

        if not (200 <= response.status_code < 300):
            # Invalid response
            return False

        user = ElementTree.fromstring(response.content)

        # Update user details
        self.thumb = user.attrib.get('thumb')

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
            'username': self.username
        }

        if not full:
            return result

        # Merge authorization details
        result['authorization'] = {
            'basic': {'valid': False}
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

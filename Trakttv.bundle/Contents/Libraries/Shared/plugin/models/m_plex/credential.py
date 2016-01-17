from plugin.core.environment import Environment
from plugin.models.m_plex.account import PlexAccount
from plugin.models.core import db

from playhouse.apsw_ext import *
from xml.etree import ElementTree
import logging
import requests

log = logging.getLogger(__name__)


class PlexBasicCredential(Model):
    class Meta:
        database = db
        db_table = 'plex.credential.basic'

    account = ForeignKeyField(PlexAccount, 'basic_credentials', unique=True)

    password = CharField(null=True)

    # Authorization
    token_plex = CharField(null=True)
    token_server = CharField(null=True)

    @property
    def state(self):
        if self.token_plex is not None and self.token_server is not None:
            return 'valid'

        if self.password is not None:
            return 'warning'

        return 'empty'

    def refresh(self, save=True):
        # Refresh account details
        if not self.refresh_details():
            return False

        # Store changes in database
        if save:
            self.save()

        return True

    def refresh_details(self):
        if self.token_plex is None:
            # Missing token
            return False

        if self.token_server is not None:
            # Already authenticated
            return True

        if self.token_plex == 'anonymous':
            return self.refresh_anonymous()

        # Fetch server token
        response = requests.get('https://plex.tv/api/resources?includeHttps=1', headers={
            'X-Plex-Token': self.token_plex
        })

        if not (200 <= response.status_code < 300):
            # Invalid response
            return False

        devices = ElementTree.fromstring(response.content)

        # Find server
        server = None

        for s in devices.findall('Device'):
            if s.attrib.get('clientIdentifier') != Environment.platform.machine_identifier:
                continue

            server = s

        if server is None:
            log.warn('Unable to find server with identifier: %r', Environment.platform.machine_identifier)
            return False

        # Update `token_server`
        self.token_server = server.attrib.get('accessToken')

        return True

    def refresh_anonymous(self):
        log.debug('Refreshing anonymous plex credential')

        self.token_server = 'anonymous'

        return True

    def to_json(self, account):
        result = {
            'state': self.state,

            'username': account.username
        }

        if self.password:
            result['password'] = '*' * len(self.password)
        elif self.token_plex:
            result['password'] = '*' * 8

        return result

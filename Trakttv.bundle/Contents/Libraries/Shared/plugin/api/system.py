from plugin.api.core.base import Service, expose
from plugin.core.constants import PLUGIN_VERSION
from plugin.core.environment import Environment

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from xml.etree import ElementTree
import logging
import os
import requests

log = logging.getLogger(__name__)


class SystemService(Service):
    __key__ = 'system'

    def __init__(self, manager):
        super(SystemService, self).__init__(manager)

        self._serializers = {
            'access': self._build_serializer(7 * 86400, 'authenticate'),  # access tokens expire in 7 days
        }

    @expose(authenticated=False)
    def authenticate(self, plex_token):
        serializer = self._serializers['access']

        if not serializer:
            raise Exception('Serializer not available')

        # Retrieve account details
        account = self._get_account(plex_token)

        # Ensure account is an administrator
        server = self._get_server(plex_token)

        if server.get('owned') != '1':
            raise Exception('Only server administrators have access to the API')

        # Construct token
        header, token = self._generate_token(serializer, {
            'username': account.get('username')
        })

        # Construct response
        return {
            'X-Channel-Token':           token,
            'X-Channel-Token-Expire':    header['exp']
        }

    @expose(authenticated=False)
    def test(self, *args, **kwargs):
        return {
            'args': args,
            'kwargs': kwargs
        }

    @expose(authenticated=False)
    def ping(self):
        result = {
            'version': PLUGIN_VERSION
        }

        if self.context.token:
            result['token'] = {
                'username': self.context.token['username']
            }

        return result

    def validate(self, token):
        serializer = self._serializers['access']

        if not serializer:
            raise Exception('Serializer not available')

        return serializer.loads(token)

    @staticmethod
    def _build_serializer(expires_in, salt):
        if not Environment.dict['api.secret']:
            # Generate secret key
            Environment.dict['api.secret'] = os.urandom(50).encode('hex')
            Environment.dict.Save()

        return Serializer(
            Environment.dict['api.secret'],
            expires_in=expires_in,
            salt=salt
        )

    @staticmethod
    def _generate_token(serializer, data):
        # Construct token
        header = serializer.make_header(None)
        signer = serializer.make_signer(serializer.salt, serializer.algorithm)

        # Generate token from header + data
        token = signer.sign(serializer.dump_payload(header, data))

        return header, token

    @staticmethod
    def _get_account(plex_token):
        response = requests.get('https://plex.tv/users/account', headers={
            'X-Plex-Token': plex_token
        })

        # Parse response
        if response.status_code != 200:
            raise Exception('Unable to retrieve account details')

        return ElementTree.fromstring(response.content)

    @staticmethod
    def _get_server(plex_token):
        response = requests.get('https://plex.tv/api/resources?includeHttps=1', headers={
            'X-Plex-Token': plex_token
        })

        # Parse response
        if response.status_code != 200:
            raise Exception('Validation request failed')

        servers = ElementTree.fromstring(response.content)

        # Find local server
        for server in servers.findall('Device'):
            if server.get('clientIdentifier') != Environment.platform.machine_identifier:
                continue

            return server

        raise Exception('Unable to retrieve server details')

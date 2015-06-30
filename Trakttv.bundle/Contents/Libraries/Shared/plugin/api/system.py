from plugin.api.core.base import Service, expose
from plugin.core.constants import PLUGIN_VERSION
from plugin.core.environment import Environment

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from xml.etree import ElementTree
import logging
import os
import requests

log = logging.getLogger(__name__)


class System(Service):
    __key__ = 'system'

    def __init__(self, manager):
        super(System, self).__init__(manager)

        self._serializers = {
            'access': self._build_serializer(7 * 86400, 'authenticate'),  # access tokens expire in 7 days
        }

    @expose(authenticated=False)
    def authenticate(self, plex_token):
        serializer = self._serializers['access']

        if not serializer:
            raise Exception('Serializer not available')

        # Validate `plex_token` via plex.tv
        response = requests.get('https://plex.tv/users/account', headers={
            'X-Plex-Token': plex_token
        })

        if response.status_code != 200:
            raise Exception('Validation request failed')

        # Parse response
        account = ElementTree.fromstring(response.content)

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

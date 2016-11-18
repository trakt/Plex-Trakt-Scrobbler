from plugin.managers.core.base import Manager, Update
from plugin.models import TraktBasicCredential, TraktOAuthCredential

from trakt import Trakt
import inspect
import logging

log = logging.getLogger(__name__)


class UpdateBasicCredential(Update):
    keys = ['password', 'token']

    def from_dict(self, basic_credential, changes, save=True):
        # Resolve `basic_credential`
        if inspect.isfunction(basic_credential):
            basic_credential = basic_credential()

        # Request new token on credential changes
        if 'username' in changes or 'password' in changes:
            # Retrieve credentials
            username = changes.get('username', basic_credential.account.username)
            password = changes.get('password', basic_credential.password)

            # Retrieve new token
            changes['token'] = Trakt['auth'].login(username, password)

        # Update `TraktBasicCredential`
        if not super(UpdateBasicCredential, self).from_dict(basic_credential, changes, save=save):
            return False

        return True


class TraktBasicCredentialManager(Manager):
    update = UpdateBasicCredential

    model = TraktBasicCredential

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve basic credential
        try:
            credential = cls.get(*query, **kwargs)
        except Exception as ex:
            log.warn('Unable to find basic credential (query: %r, kwargs: %r): %r', query, kwargs, ex)
            return False

        # Clear basic credential
        cls.update(credential, {
            'password': None,

            'token': None
        })

        return True


class UpdateOAuthCredential(Update):
    keys = ['code', 'access_token', 'refresh_token', 'created_at', 'expires_in', 'token_type', 'scope']

    def from_dict(self, oauth_credential, changes, save=True):
        # Update `TraktOAuthCredential`
        if not super(UpdateOAuthCredential, self).from_dict(oauth_credential, changes, save=save):
            return False

        return True

    def from_pin(self, oauth, pin, save=True):
        # Exchange `pin` for token authorization
        authorization = Trakt['oauth'].token_exchange(pin, 'urn:ietf:wg:oauth:2.0:oob')

        if not authorization:
            log.warn('Token exchange failed')
            return None

        # Update `OAuthCredential`
        data = {'code': pin}
        data.update(authorization)

        return self(oauth, data, save=save)


class TraktOAuthCredentialManager(Manager):
    update = UpdateOAuthCredential

    model = TraktOAuthCredential

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve oauth credential
        try:
            credential = cls.get(*query, **kwargs)
        except Exception as ex:
            log.warn('Unable to find oauth credential (query: %r, kwargs: %r): %r', query, kwargs, ex)
            return False

        # Clear oauth credential
        cls.update(credential, {
            'code': None,

            'access_token': None,
            'refresh_token': None,

            'created_at': None,
            'expires_in': None,

            'token_type': None,
            'scope': None
        })

        return True

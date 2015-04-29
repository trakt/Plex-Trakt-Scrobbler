from plugin.managers.core.base import Manager, Update
from plugin.models import TraktBasicCredential, TraktOAuthCredential

from trakt import Trakt
import inspect
import logging

log = logging.getLogger(__name__)


class UpdateBasicCredential(Update):
    def from_dict(self, basic_credential, changes):
        log.debug('from_dict(%r, %r)', basic_credential, changes)

        if not changes:
            return False

        # Resolve `basic_credential`
        if inspect.isfunction(basic_credential):
            basic_credential = basic_credential()

        # Update `TraktBasicCredential`
        data = {}

        if 'password' in changes:
            data['password'] = changes['password']

        if 'token' in changes:
            data['token'] = changes['token']

        if data and not self(basic_credential, data):
            # Unable to update `TraktBasicCredential`
            return False

        return True


class TraktBasicCredentialManager(Manager):
    update = UpdateBasicCredential

    model = TraktBasicCredential


class UpdateOAuthCredential(Update):
    allowed_keys = ['code', 'access_token', 'refresh_token', 'created_at', 'expires_in', 'token_type', 'scope']

    def from_dict(self, oauth_credential, changes):
        log.debug('from_dict(%r, %r)', oauth_credential, changes)

        if not changes:
            return False

        # Resolve `basic_credential`
        if inspect.isfunction(oauth_credential):
            oauth_credential = oauth_credential()

        # Update `TraktOAuthCredential`
        data = {}

        for key in self.allowed_keys:
            if key not in changes:
                continue

            data[key] = changes[key]

        if data and not self(oauth_credential, data):
            # Unable to update `TraktOAuthCredential`
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

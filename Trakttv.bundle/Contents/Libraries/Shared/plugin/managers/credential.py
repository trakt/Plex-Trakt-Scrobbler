from plugin.managers.core.base import Manager, Update
from plugin.models import BasicCredential, OAuthCredential

from trakt import Trakt
import logging

log = logging.getLogger(__name__)


class BasicCredentialManager(Manager):
    model = BasicCredential


class UpdateOAuthCredential(Update):
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


class OAuthCredentialManager(Manager):
    update = UpdateOAuthCredential

    model = OAuthCredential

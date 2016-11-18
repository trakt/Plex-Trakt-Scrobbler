from plugin.managers.core.base import Manager, Update
from plugin.models import PlexBasicCredential

import logging

log = logging.getLogger(__name__)


class UpdateBasicCredential(Update):
    keys = ['password', 'token_plex']

    def from_dict(self, basic_credential, changes, save=True):
        # Update `PlexBasicCredential`
        if not super(UpdateBasicCredential, self).from_dict(basic_credential, changes, save=save):
            return False

        return True


class PlexBasicCredentialManager(Manager):
    update = UpdateBasicCredential

    model = PlexBasicCredential

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

            'token_plex': None,
            'token_server': None
        })

        return True

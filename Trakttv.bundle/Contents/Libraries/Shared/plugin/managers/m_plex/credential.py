from plugin.managers.core.base import Manager, Update
from plugin.models import PlexBasicCredential

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

        # Update `PlexBasicCredential`
        data = {}

        if 'password' in changes:
            data['password'] = changes['password']

        if 'token' in changes:
            data['token'] = changes['token']

        if data and not self(basic_credential, data):
            # Unable to update `PlexBasicCredential`
            return False

        return True


class PlexBasicCredentialManager(Manager):
    update = UpdateBasicCredential

    model = PlexBasicCredential

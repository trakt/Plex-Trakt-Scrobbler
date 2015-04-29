from plugin.managers.core.base import Manager, Update
from plugin.models import PlexBasicCredential

import logging

log = logging.getLogger(__name__)


class UpdateBasicCredential(Update):
    keys = ['password', 'token']

    def from_dict(self, basic_credential, changes):
        # Update `PlexBasicCredential`
        if not super(UpdateBasicCredential, self).from_dict(basic_credential, changes):
            return False

        return True


class PlexBasicCredentialManager(Manager):
    update = UpdateBasicCredential

    model = PlexBasicCredential

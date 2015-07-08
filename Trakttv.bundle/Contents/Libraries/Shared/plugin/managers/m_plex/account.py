from plugin.managers.core.base import Manager, Update
from plugin.managers.m_plex.credential import PlexBasicCredentialManager
from plugin.models import PlexAccount, PlexBasicCredential

import inspect
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    keys = ['username']

    def from_dict(self, account, changes):
        # Resolve `account`
        if inspect.isfunction(account):
            account = account()

        # Update `PlexAccount`
        if not super(UpdateAccount, self).from_dict(account, changes):
            return False

        # Update `PlexBasicCredential`
        PlexBasicCredentialManager.update.from_dict(
            lambda: PlexBasicCredentialManager.get.or_create(
                PlexBasicCredential.account == account,
                account=account
            ),
            changes.get('authorization', {}).get('basic', {})
        )

        return True


class PlexAccountManager(Manager):
    update = UpdateAccount

    model = PlexAccount

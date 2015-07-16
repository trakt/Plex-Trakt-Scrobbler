from plugin.managers.core.base import Manager, Update
from plugin.managers.m_plex.credential import PlexBasicCredentialManager
from plugin.models import PlexAccount, PlexBasicCredential

import inspect
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    keys = ['username']

    def from_dict(self, p_account, changes):
        # Resolve `account`
        if inspect.isfunction(p_account):
            p_account = p_account()

        # Update `PlexAccount`
        if not super(UpdateAccount, self).from_dict(p_account, changes):
            return False

        # Update `PlexBasicCredential`
        PlexBasicCredentialManager.update.from_dict(
            lambda: PlexBasicCredentialManager.get.or_create(
                PlexBasicCredential.account == p_account,
                account=p_account
            ),
            changes.get('authorization', {}).get('basic', {})
        )

        # Refresh `TraktAccount`
        p_account.refresh(
            force=True
        )

        # Refresh `Account`
        p_account.account.refresh()

        return True


class PlexAccountManager(Manager):
    update = UpdateAccount

    model = PlexAccount

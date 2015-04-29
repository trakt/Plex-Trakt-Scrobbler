from plugin.managers.core.base import Manager, Update
from plugin.managers.m_plex.credential import PlexBasicCredentialManager
from plugin.models import PlexAccount, PlexBasicCredential

import inspect
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    def from_dict(self, account, changes):
        log.debug('from_api(%r, %r)', account, changes)

        if not changes:
            return False

        # Resolve `account`
        if inspect.isfunction(account):
            account = account()

        # Update `PlexAccount`
        data = {}

        if 'username' in changes:
            data['username'] = changes['username']

        if data and not self(account, data):
            log.debug('Unable to update %r (nothing changed?)', account)

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

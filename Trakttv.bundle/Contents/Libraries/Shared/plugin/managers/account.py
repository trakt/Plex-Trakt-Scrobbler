from plugin.managers import PlexAccountManager, TraktAccountManager
from plugin.managers.core.base import Manager, Update
from plugin.models import Account, TraktAccount, PlexAccount
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    def from_dict(self, account, changes):
        log.debug('from_api(%r, %r)', account, changes)

        if not changes:
            return False

        # Update `Account`
        data = {}

        if 'name' in changes:
            data['name'] = changes['name']

        if data and not self(account, data):
            # Unable to update `Account`
            return False

        # Update `PlexAccount`
        PlexAccountManager.update.from_dict(
            lambda: PlexAccountManager.get.or_create(
                PlexAccount.account == account,
                account=account
            ),
            changes.get('plex', {})
        )

        # Update `TraktAccount`
        TraktAccountManager.update.from_dict(
            lambda: TraktAccountManager.get.or_create(
                TraktAccount.account == account,
                account=account
            ),
            changes.get('trakt', {})
        )

        return True


class AccountManager(Manager):
    update = UpdateAccount

    model = Account

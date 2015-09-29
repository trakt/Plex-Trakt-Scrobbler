from plugin.managers import PlexAccountManager, TraktAccountManager
from plugin.managers.core.base import Manager, Update
from plugin.models import Account, TraktAccount, PlexAccount
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    def from_dict(self, account, changes):
        if not changes:
            return False

        # Update `Account`
        data = {}

        if 'name' in changes:
            data['name'] = changes['name']

        if data and self(account, data):
            log.debug('Updated account')

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

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve account
        account = cls.get(*query, **kwargs)

        if not account:
            log.warn('Unable to find account (query: %r, kwargs: %r)', query, kwargs)
            return False

        if account.deleted:
            return True

        # Clear account
        cls.update(account, {
            'name': None,
            'thumb': None,

            'deleted': True,
            'refreshed_at': None
        })

        # Delete `PlexAccount`
        PlexAccountManager.delete(
            account=account.id
        )

        # Delete `TraktAccount`
        TraktAccountManager.delete(
            account=account.id
        )

        return True

from plugin.managers.core.base import Manager, Update
from plugin.managers.core.exceptions import PlexAccountExistsException
from plugin.managers.m_plex.credential import PlexBasicCredentialManager
from plugin.models import PlexAccount, PlexBasicCredential

from exception_wrappers.libraries import apsw
import inspect
import logging
import peewee


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    keys = ['username']

    def from_dict(self, p_account, changes):
        # Resolve `account`
        if inspect.isfunction(p_account):
            p_account = p_account()

        # Update `PlexAccount`
        username = changes.pop('username', None)

        if not super(UpdateAccount, self).from_dict(p_account, changes):
            return False

        # Update credentials
        authorization = changes.get('authorization', {})

        # Update `PlexBasicCredential`
        p_account.basic = PlexBasicCredentialManager.get.or_create(
            PlexBasicCredential.account == p_account,
            account=p_account
        )

        # Update `TraktBasicCredential` (if there are changes)
        if 'basic' in authorization:
            PlexBasicCredentialManager.update.from_dict(
                p_account.basic,
                authorization['basic'],
                save=False
            )

        # Update `PlexAccount` username
        try:
            self.update_username(p_account, username)
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            log.debug('Plex account already exists - %s', ex, exc_info=True)

            raise PlexAccountExistsException('Plex account already exists')

        # Refresh `TraktAccount`
        p_account.refresh(
            force=True
        )

        # Save credentials
        if 'basic' in authorization:
            p_account.basic.save()

        # Refresh `Account`
        p_account.account.refresh(
            force=True
        )

        log.info('Updated account authorization for %r', p_account)
        return True

    def update_username(self, p_account, username, save=True):
        self(p_account, {'username': username}, save=save)


class PlexAccountManager(Manager):
    update = UpdateAccount

    model = PlexAccount

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve account
        try:
            account = cls.get(*query, **kwargs)
        except Exception as ex:
            log.warn('Unable to find plex account (query: %r, kwargs: %r): %r', query, kwargs, ex)
            return False

        # Clear plex account
        cls.update(account, {
            'key': None,
            'username': None,

            'title': None,
            'thumb': None,

            'refreshed_at': None
        })

        # Delete plex credentials
        PlexBasicCredentialManager.delete(
            account=account.id
        )

        return True

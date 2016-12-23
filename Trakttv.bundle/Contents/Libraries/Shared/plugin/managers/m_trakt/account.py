from plugin.managers.core.base import Manager, Update
from plugin.managers.core.exceptions import TraktAccountExistsException
from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager, TraktBasicCredentialManager
from plugin.models import TraktAccount, TraktOAuthCredential, TraktBasicCredential

from exception_wrappers.libraries import apsw
from trakt import Trakt
import inspect
import logging
import peewee


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    keys = ['username']

    def from_dict(self, t_account, changes, settings=None):
        # Resolve `account`
        if inspect.isfunction(t_account):
            t_account = t_account()

        # Update `TraktAccount`
        if not super(UpdateAccount, self).from_dict(t_account, changes):
            return False

        # Update credentials
        authorization = changes.get('authorization', {})

        if 'username' in changes:
            # Provide username change in basic authorization update
            if 'basic' not in authorization:
                authorization['basic'] = {}

            authorization['basic']['username'] = changes['username']

        # Retrieve `TraktBasicCredential`
        t_account.basic = TraktBasicCredentialManager.get.or_create(
            TraktBasicCredential.account == t_account,
            account=t_account
        )

        # Update `TraktBasicCredential` (if there are changes)
        if 'basic' in authorization:
            TraktBasicCredentialManager.update.from_dict(
                t_account.basic,
                authorization['basic'],
                save=False
            )

        # Retrieve `TraktOAuthCredential`
        t_account.oauth = TraktOAuthCredentialManager.get.or_create(
            TraktOAuthCredential.account == t_account,
            account=t_account
        )

        # Update `TraktOAuthCredential` (if there are changes)
        if 'oauth' in authorization:
            TraktOAuthCredentialManager.update.from_dict(
                t_account.oauth,
                authorization['oauth'],
                save=False
            )

        # Fetch account settings (if not provided)
        if not settings:
            with t_account.authorization().http(retry=True):
                settings = Trakt['users/settings'].get()

        # Ensure account settings are available
        if not settings:
            log.warn('Unable to retrieve account details for authorization')
            return None

        # Update `TraktAccount` username
        try:
            self.update_username(t_account, settings)
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            log.debug('Trakt account already exists - %s', ex, exc_info=True)

            raise TraktAccountExistsException('Trakt account already exists')

        # Refresh `TraktAccount`
        t_account.refresh(
            force=True,
            settings=settings
        )

        # Save credentials
        if 'basic' in authorization:
            t_account.basic.save()

        if 'oauth' in authorization:
            t_account.oauth.save()

        # Refresh `Account`
        t_account.account.refresh(
            force=True
        )

        log.info('Updated account authorization for %r', t_account)
        return True

    def from_pin(self, t_account, pin):
        if not pin:
            log.debug('"pin" parameter is empty, ignoring account authorization update')
            return t_account

        # Retrieve current account `OAuthCredential`
        oauth = t_account.oauth_credentials.first()

        if oauth and oauth.code == pin:
            log.debug("PIN hasn't changed, ignoring account authorization update")
            return t_account

        if not oauth:
            # Create new `OAuthCredential` for the account
            oauth = TraktOAuthCredential(
                account=t_account
            )

        # Update `OAuthCredential`
        if not TraktOAuthCredentialManager.update.from_pin(oauth, pin, save=False):
            log.warn("Unable to update OAuthCredential (token exchange failed, hasn't changed, etc..)")

            # Save code into database (to avoid future re-authentication with the same pin)
            oauth.save()
            return None

        # Validate the account authorization
        with t_account.oauth_authorization(oauth).http(retry=True):
            settings = Trakt['users/settings'].get()

        if not settings:
            log.warn('Unable to retrieve account details for authorization')
            return None

        # Update `TraktAccount` username
        try:
            self.update_username(t_account, settings)
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            log.debug('Trakt account already exists - %s', ex, exc_info=True)

            raise TraktAccountExistsException('Trakt account already exists')

        # Save oauth credential changes
        oauth.save()

        # Refresh `TraktAccount`
        t_account.refresh(
            force=True,
            settings=settings
        )

        # Refresh `Account`
        t_account.account.refresh(
            force=True
        )

        log.info('Updated account authorization for %r', t_account)
        return t_account

    def update_username(self, t_account, settings, save=True):
        username = settings.get('user', {}).get('username')

        if not username:
            log.warn('Unable to retrieve username for authorization')
            return

        if t_account.username == username:
            return

        self(t_account, {'username': username}, save=save)


class TraktAccountManager(Manager):
    update = UpdateAccount

    model = TraktAccount

    @classmethod
    def delete(cls, *query, **kwargs):
        # Retrieve account
        try:
            account = cls.get(*query, **kwargs)
        except Exception as ex:
            log.warn('Unable to find trakt account (query: %r, kwargs: %r): %r', query, kwargs, ex)
            return False

        # Clear trakt account
        cls.update(account, {
            'username': None,
            'thumb': None,

            'cover': None,
            'timezone': None,

            'refreshed_at': None
        })

        # Delete trakt credentials
        TraktBasicCredentialManager.delete(
            account=account.id
        )

        TraktOAuthCredentialManager.delete(
            account=account.id
        )

        return True

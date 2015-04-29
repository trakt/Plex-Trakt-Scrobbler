from plugin.managers.core.base import Manager, Update
from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager, TraktBasicCredentialManager
from plugin.models import TraktAccount, TraktOAuthCredential, TraktBasicCredential

from trakt import Trakt
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

        # Update `TraktAccount`
        data = {}

        if 'username' in changes:
            data['username'] = changes['username']

        if data and not self(account, data):
            log.debug('Unable to update %r (nothing changed?)', account)

        # Update `TraktBasicCredential`
        TraktBasicCredentialManager.update.from_dict(
            lambda: TraktBasicCredentialManager.get.or_create(
                TraktBasicCredential.account == account,
                account=account
            ),
            changes.get('authorization', {}).get('basic', {})
        )

        # Update `TraktOAuthCredential`
        TraktOAuthCredentialManager.update.from_dict(
            lambda: TraktBasicCredentialManager.get.or_create(
                TraktOAuthCredential.account == account,
                account=account
            ),
            changes.get('authorization', {}).get('oauth', {})
        )

        return False

    def from_pin(self, account, pin):
        if not pin:
            log.debug('"pin" parameter is empty, ignoring account authorization update')
            return account

        # Retrieve current account `OAuthCredential`
        oauth = account.oauth_credentials.first()

        if oauth and oauth.code == pin:
            log.debug("PIN hasn't changed, ignoring account authorization update")
            return account

        if not oauth:
            # Create new `OAuthCredential` for the account
            oauth = TraktOAuthCredential(
                account=account
            )

        # Update `OAuthCredential`
        if not TraktOAuthCredentialManager.update.from_pin(oauth, pin, save=False):
            log.warn("Unable to update OAuthCredential (token exchange failed, hasn't changed, etc..)")
            return None

        # Validate the account authorization
        with account.oauth_authorization(oauth):
            settings = Trakt['users/settings'].get()

        if not settings:
            log.warn('Unable to retrieve account details for authorization')
            return None

        username = settings.get('user', {}).get('username')

        if not username:
            log.warn('Unable to retrieve username for authorization')
            return None

        self(account, {'username': username}, save=False)

        # Save `OAuthCredential` and `Account`
        oauth.save()
        account.save()

        log.info('Updated account authorization for %r', account)
        return account


class TraktAccountManager(Manager):
    update = UpdateAccount

    model = TraktAccount

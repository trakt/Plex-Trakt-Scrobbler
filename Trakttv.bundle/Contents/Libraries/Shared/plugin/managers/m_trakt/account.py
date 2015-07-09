from plugin.managers.core.base import Manager, Update
from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager, TraktBasicCredentialManager
from plugin.models import TraktAccount, TraktOAuthCredential, TraktBasicCredential

from trakt import Trakt
import inspect
import logging


log = logging.getLogger(__name__)


class UpdateAccount(Update):
    keys = ['username']

    def from_dict(self, t_account, changes):
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

        # Update `TraktBasicCredential` (if there are changes)
        if 'basic' in authorization:
            TraktBasicCredentialManager.update.from_dict(
                lambda: TraktBasicCredentialManager.get.or_create(
                    TraktBasicCredential.account == t_account,
                    account=t_account
                ),
                authorization['basic']
            )

        # Update `TraktOAuthCredential` (if there are changes)
        if 'oauth' in authorization:
            TraktOAuthCredentialManager.update.from_dict(
                lambda: TraktOAuthCredentialManager.get.or_create(
                    TraktOAuthCredential.account == t_account,
                    account=t_account
                ),
                authorization['oauth']
            )

        # Refresh details
        t_account.refresh()
        t_account.account.refresh()

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
            return None

        # Validate the account authorization
        with t_account.oauth_authorization(oauth):
            settings = Trakt['users/settings'].get()

        if not settings:
            log.warn('Unable to retrieve account details for authorization')
            return None

        username = settings.get('user', {}).get('username')

        if not username:
            log.warn('Unable to retrieve username for authorization')
            return None

        self(t_account, {'username': username}, save=False)

        t_account.refresh(
            force=True, save=False,
            settings=settings
        )

        # Save `OAuthCredential` and `Account`
        oauth.save()
        t_account.save()

        # Refresh `Account`
        t_account.account.refresh()

        log.info('Updated account authorization for %r', t_account)
        return t_account


class TraktAccountManager(Manager):
    update = UpdateAccount

    model = TraktAccount

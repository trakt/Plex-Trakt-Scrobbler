from plugin.core.environment import Environment
from plugin.models import (
    Account, ClientRule, UserRule,
    PlexAccount, PlexBasicCredential,
    TraktAccount, TraktBasicCredential, TraktOAuthCredential
)
from plugin.modules.migrations.core.base import Migration

from exception_wrappers.libraries import apsw
import logging
import os
import peewee
import requests

log = logging.getLogger(__name__)


class AccountMigration(Migration):
    def run(self, token_plex=None):
        # Ensure server `Account` exists
        self.create_server_account()

        # Ensure administrator `Account` exists
        self.create_administrator_account(token_plex=token_plex)

        # Refresh extra accounts
        accounts = Account.select().where(
            Account.id > 1,
            Account.deleted == False
        )

        for account in accounts:
            self.refresh_account(account)

        return True

    @classmethod
    def create_server_account(cls):
        try:
            Account.get(Account.id == 0)
        except Account.DoesNotExist:
            Account.create(
                id=0,
                name=''
            )

    @classmethod
    def create_administrator_account(cls, token_plex=None):
        username = cls.get_trakt_username()

        try:
            account = Account.get(Account.id == 1)
        except Account.DoesNotExist:
            account = Account.create(
                id=1,
                name=username
            )

            # Create default rules for account
            cls.create_rules(account)

        # Ensure plex account details exist
        p_created, p_account = cls.create_plex_account(account)

        cls.create_plex_basic_credential(p_account, token_plex=token_plex)

        # Refresh plex account details
        try:
            p_refreshed = p_account.refresh(force=p_created)
        except:
            log.warn('Unable to refresh plex account (not authenticated?)', exc_info=True)
            p_refreshed = False

        # Ensure trakt account details exist
        t_created, t_account = cls.create_trakt_account(account, username)

        cls.create_trakt_basic_credential(t_account)
        cls.create_trakt_oauth_credential(t_account)

        # Refresh trakt account details
        try:
            t_refreshed = t_account.refresh(force=t_created)
        except:
            log.warn('Unable to refresh trakt account (not authenticated?)', exc_info=True)
            t_refreshed = False

        # Refresh account
        account.refresh(force=p_refreshed or t_refreshed)

    @classmethod
    def refresh_account(cls, account):
        if not account or account.deleted:
            return

        log.debug('Refreshing account: %r', account)

        # Refresh plex account details
        p_account = account.plex
        p_refreshed = False

        if p_account:
            try:
                p_refreshed = p_account.refresh()
            except:
                log.info('Unable to refresh plex account (not authenticated?)', exc_info=True)
                p_refreshed = False

        # Refresh trakt account details
        t_account = account.trakt
        t_refreshed = False

        if t_account:
            try:
                t_refreshed = t_account.refresh()
            except:
                log.info('Unable to refresh trakt account (not authenticated?)', exc_info=True)
                t_refreshed = False

        # Refresh account
        account.refresh(force=p_refreshed or t_refreshed)

    @classmethod
    def create_rules(cls, account):
        ClientRule.create(account=account, priority=1)
        UserRule.create(account=account, priority=1)

    #
    # Plex
    #

    @classmethod
    def create_plex_account(cls, account):
        try:
            return True, PlexAccount.create(
                account=account
            )
        except (apsw.ConstraintError, peewee.IntegrityError):
            return False, PlexAccount.get(
                account=account
            )

    @classmethod
    def create_plex_basic_credential(cls, plex_account, token_plex=None):
        if token_plex is None:
            token_plex = cls.get_token()

        if not token_plex:
            log.warn('No plex token available, unable to authenticate plex account')
            return False

        try:
            PlexBasicCredential.create(
                account=plex_account,

                token_plex=token_plex
            )
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            # Ensure basic credential has a token
            rows_updated = PlexBasicCredential.update(
                token_plex=token_plex,
                token_server=None
            ).where(
                PlexBasicCredential.account == plex_account,
                PlexBasicCredential.token_plex != token_plex
            ).execute()

            # Check if basic credential was updated
            if rows_updated:
                return True

            log.debug('Ignoring basic credential update for %r, already exists (%s)', plex_account, ex)
            return False

        return True

    #
    # Trakt
    #

    @classmethod
    def create_trakt_account(cls, account, username):
        try:
            return True, TraktAccount.create(
                account=account,
                username=username
            )
        except (apsw.ConstraintError, peewee.IntegrityError):
            return False, TraktAccount.get(
                account=account
            )

    @classmethod
    def create_trakt_basic_credential(cls, trakt_account):
        if not Environment.dict['trakt.token']:
            return False

        try:
            TraktBasicCredential.create(
                account=trakt_account,
                password=Environment.get_pref('password'),

                token=Environment.dict['trakt.token']
            )
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            log.debug('Ignoring basic credential update for %r, already exists (%s)', trakt_account, ex)
            return False

        return True

    @classmethod
    def create_trakt_oauth_credential(cls, trakt_account):
        if not Environment.dict['trakt.pin.code'] or not Environment.dict['trakt.pin.authorization']:
            return False

        try:
            TraktOAuthCredential.create(
                account=trakt_account,
                code=Environment.dict['trakt.pin.code'],

                **Environment.dict['trakt.pin.authorization']
            )
        except (apsw.ConstraintError, peewee.IntegrityError) as ex:
            log.debug('Ignoring oauth credential update for %r, already exists (%s)', trakt_account, ex)
            return False

        return True

    @classmethod
    def get_trakt_username(cls):
        if Environment.get_pref('username'):
            return Environment.get_pref('username')

        if Environment.dict['trakt.username']:
            return Environment.dict['trakt.username']

        return None

    @classmethod
    def get_token(cls, request_headers=None):
        # Environment token
        env_token = os.environ.get('PLEXTOKEN')

        if env_token:
            log.info('Plex Token: environment')
            return env_token

        # Check if anonymous access is available
        server = requests.get('http://localhost:32400')

        if server.status_code == 200:
            log.info('Plex Token: anonymous')
            return 'anonymous'

        # No token available
        if request_headers is None:
            log.error('Plex Token: not available')
            return None

        # Try retrieve token from request
        req_token = request_headers.get('X-Plex-Token')

        if req_token:
            log.info('Plex Token: request')
            return req_token

        # No token available in request
        data = {
            'Client': {
                'User-Agent': request_headers.get('User-Agent'),
                'X-Plex-Product': request_headers.get('X-Plex-Product'),
            },
            'Headers': request_headers.keys()
        }

        log.debug('Request details: %r', data)
        log.error('Plex Token: not available', extra={
            'data': data
        })
        return None

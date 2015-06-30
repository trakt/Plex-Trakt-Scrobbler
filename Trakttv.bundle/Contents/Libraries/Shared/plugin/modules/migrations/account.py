from plugin.core.environment import Environment
from plugin.models import (
    Account, ClientRule, UserRule,
    PlexAccount, PlexBasicCredential,
    TraktAccount, TraktBasicCredential, TraktOAuthCredential
)
from plugin.modules.migrations.core.base import Migration

from xml.etree import ElementTree
import apsw
import logging
import os
import peewee
import requests

log = logging.getLogger(__name__)


class AccountMigration(Migration):
    def run(self):
        # Ensure server `Account` exists
        self.create_server_account()

        # Ensure administrator `Account` exists
        self.create_administrator_account()

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
    def create_administrator_account(cls):
        username = cls.get_trakt_username()

        if username is None:
            log.debug('Unable to migrate administrator account, no previous trakt username found')
            return

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
        plex_account = cls.create_plex_account(account)

        cls.create_plex_basic_credential(plex_account)

        # Ensure trakt account details exist
        created, trakt_account = cls.create_trakt_account(account, username)

        cls.create_trakt_basic_credential(trakt_account)
        cls.create_trakt_oauth_credential(trakt_account)

        # Refresh trakt account details
        trakt_account.refresh(force=created)

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
            return PlexAccount.get(
                account=account
            )
        except PlexAccount.DoesNotExist:
            pass

        token = os.environ.get('PLEXTOKEN')

        username = None
        thumb = None

        if token:
            user = cls.get_plex_account(token)

            username = user.attrib.get('username')
            thumb = user.attrib.get('thumb')

        return PlexAccount.create(
            id=1,  # administrator account id
            account=account,

            username=username,
            thumb=thumb
        )

    @classmethod
    def create_plex_basic_credential(cls, plex_account):
        token = os.environ.get('PLEXTOKEN')

        if not token:
            return False

        try:
            PlexBasicCredential.create(
                account=plex_account,

                token=token
            )
        except (apsw.ConstraintError, peewee.IntegrityError), ex:
            log.debug('BasicCredential for %r already exists - %s', plex_account, ex, exc_info=True)
            return False

        return True

    @classmethod
    def get_plex_account(cls, token):
        response = requests.get('https://plex.tv/users/account', headers={
            'X-Plex-Token': token
        })

        return ElementTree.fromstring(response.content)

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
        except (apsw.ConstraintError, peewee.IntegrityError), ex:
            log.debug('BasicCredential for %r already exists - %s', trakt_account, ex, exc_info=True)
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
        except (apsw.ConstraintError, peewee.IntegrityError), ex:
            log.debug('OAuthCredential for %r already exists - %s', trakt_account, ex, exc_info=True)
            return False

        return True

    @classmethod
    def get_trakt_username(cls):
        if Environment.get_pref('username'):
            return Environment.get_pref('username')

        if Environment.dict['trakt.username']:
            return Environment.dict['trakt.username']

        return None

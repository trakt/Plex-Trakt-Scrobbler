from plugin.core.environment import Environment
from plugin.core.helpers.thread import module
from plugin.models import Account, ClientRule, UserRule,\
    PlexAccount, PlexBasicCredential,\
    TraktAccount, TraktBasicCredential, TraktOAuthCredential
from plugin.models.core import db, migrations_path

from peewee_migrate.core import Router
from xml.etree import ElementTree
import apsw
import logging
import os
import requests

log = logging.getLogger(__name__)


@module(start=True, priority=0, blocking=True)
class Migrations(object):
    @classmethod
    def start(cls):
        log.debug('migrations_path: %r', migrations_path)

        # Connect to database, enable WAL
        db.connect()
        db.execute_sql('PRAGMA journal_mode=WAL;')

        # Run migrations
        router = Router(migrations_path, DATABASE=db)
        router.run()

        # Migrate account from plugin settings
        cls.account()

    #
    # Main
    #

    @classmethod
    def account(cls):
        # Ensure `Account` exists
        try:
            account = Account.get(Account.id == 1)
        except Account.DoesNotExist:
            account = Account.create(
                name=cls.get_trakt_username()
            )

            # Create default rules for account
            cls.rules(account)

        # Ensure plex account details exist
        plex_account = cls.plex_account(account)

        cls.plex_basic_credential(plex_account)

        # Ensure trakt account details exist
        trakt_account = cls.trakt_account(account)

        cls.trakt_basic_credential(trakt_account)
        cls.trakt_oauth_credential(trakt_account)

        return True

    @classmethod
    def rules(cls, account):
        ClientRule.create(account=account, priority=1)
        UserRule.create(account=account, priority=1)

    #
    # Plex
    #

    @classmethod
    def plex_account(cls, account):
        try:
            return PlexAccount.get(
                account=account
            )
        except PlexAccount.DoesNotExist:
            pass

        token = os.environ.get('PLEXTOKEN')
        username = None

        if token:
            user = cls.get_plex_account(token)
            username = user.attrib.get('username')

        return PlexAccount.create(
            id=1,  # administrator account id

            account=account,
            username=username
        )

    @classmethod
    def plex_basic_credential(cls, plex_account):
        token = os.environ.get('PLEXTOKEN')

        if not token:
            return False

        try:
            PlexBasicCredential.create(
                account=plex_account,

                token=token
            )
        except apsw.ConstraintError, ex:
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
    def trakt_account(cls, account):
        try:
            return TraktAccount.create(
                account=account,
                username=cls.get_trakt_username()
            )
        except apsw.ConstraintError:
            return TraktAccount.get(
                account=account
            )

    @classmethod
    def trakt_basic_credential(cls, trakt_account):
        if not Environment.dict['trakt.token']:
            return False

        try:
            TraktBasicCredential.create(
                account=trakt_account,
                password=Environment.get_pref('password'),

                token=Environment.dict['trakt.token']
            )
        except apsw.ConstraintError, ex:
            log.debug('BasicCredential for %r already exists - %s', trakt_account, ex, exc_info=True)
            return False

        return True

    @classmethod
    def trakt_oauth_credential(cls, trakt_account):
        if not Environment.dict['trakt.pin.code'] or not Environment.dict['trakt.pin.authorization']:
            return False

        try:
            TraktOAuthCredential.create(
                account=trakt_account,
                code=Environment.dict['trakt.pin.code'],

                **Environment.dict['trakt.pin.authorization']
            )
        except apsw.ConstraintError, ex:
            log.debug('OAuthCredential for %r already exists - %s', trakt_account, ex, exc_info=True)
            return False

        return True

    @classmethod
    def get_trakt_username(cls):
        if Environment.get_pref('username'):
            return Environment.get_pref('username')

        if Environment.dict['trakt.username']:
            return Environment.dict['trakt.username']

        raise NotImplementedError()

from plugin.core.environment import Environment
from plugin.core.helpers.thread import module
from plugin.models import Account, ClientRule, UserRule, BasicCredential, OAuthCredential
from plugin.models.core import db, db_path, migrations_path

from peewee_migrate.core import Router
import apsw
import logging

log = logging.getLogger(__name__)


@module(start=True, priority=0, blocking=True)
class Migrations(object):
    @classmethod
    def start(cls):
        log.debug('db_path: %r', db_path)
        log.debug('migrations_path: %r', migrations_path)

        # Connect to database, enable WAL
        db.connect()
        db.execute_sql('PRAGMA journal_mode=WAL;')

        # Run migrations
        router = Router(migrations_path, DATABASE=db)
        router.run()

        # Migrate account from plugin settings
        cls.account()

    @classmethod
    def get_username(cls):
        if Environment.get_pref('username'):
            return Environment.get_pref('username')

        if Environment.dict['trakt.username']:
            return Environment.dict['trakt.username']

        raise NotImplementedError()

    @classmethod
    def account(cls):
        username = cls.get_username()

        # Get or create `Account`
        try:
            account = Account.get(Account.id == 1)
        except Account.DoesNotExist:
            account = None

        if account:
            log.debug('Account already exists, ignoring account migration')
            return False

        # Create new `Account`
        account = Account.create(
            username=username
        )

        # Create default rules for account
        cls.rules(account)

        # Create credentials
        cls.basic_credential(account)
        cls.oauth_credential(account)

        return True

    @classmethod
    def basic_credential(cls, account):
        if not Environment.dict['trakt.token']:
            return False

        try:
            BasicCredential.create(
                account=account,
                password=Environment.get_pref('password'),

                token=Environment.dict['trakt.token']
            )
        except apsw.ConstraintError:
            log.debug('BasicCredential for %r already exists', account)
            return False

        return True

    @classmethod
    def oauth_credential(cls, account):
        if not Environment.dict['trakt.pin.code'] or not Environment.dict['trakt.pin.authorization']:
            return False

        try:
            OAuthCredential.create(
                account=account,
                code=Environment.dict['trakt.pin.code'],

                **Environment.dict['trakt.pin.authorization']
            )
        except apsw.ConstraintError:
            log.debug('OAuthCredential for %r already exists', account)
            return False

        return True

    @classmethod
    def rules(cls, account):
        ClientRule.create(account=account)
        UserRule.create(account=account)

from plugin.core.environment import Environment
from plugin.core.helpers.thread import module
from plugin.models import Account, ClientRule, UserRule
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

        # Migrate from plugin settings
        cls.from_settings()

    @classmethod
    def from_settings(cls):
        username = Environment.prefs['username']
        password = Environment.prefs['password']
        token = Environment.dict['trakt.token']

        if not username or not password:
            # Invalid credentials, ignore migration
            return

        try:
            # Create `Account`
            account = Account.create(
                username=username,
                password=password,
                token=token
            )
        except apsw.ConstraintError, ex:
            log.info('Unable to migrate existing account (already migrated): %s', ex, exc_info=True)
            return False

        # Create default rules
        ClientRule.create(account=account)
        UserRule.create(account=account)

        return True

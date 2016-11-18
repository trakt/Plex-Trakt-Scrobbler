from plugin.core.helpers.thread import module
from plugin.models.core import db
from plugin.modules.migrations.account import AccountMigration
from plugin.modules.migrations.preferences import PreferencesMigration
from plugin.modules.migrations.schema import SchemaMigration

from exception_wrappers import DisabledError
import logging

log = logging.getLogger(__name__)


@module(start=True, priority=0, blocking=True)
class Migrations(object):
    migrations = [
        SchemaMigration,

        AccountMigration,
        PreferencesMigration
    ]

    @classmethod
    def start(cls):
        # Connect to database, enable WAL
        try:
            db.connect()
            db.execute_sql('PRAGMA journal_mode=WAL;')
        except DisabledError:
            return
        except Exception as ex:
            log.warn('Database connection failed: %s', ex, exc_info=True)
            return

        # Run each migration
        for migration in cls.migrations:
            m = migration()

            log.info('Running migration: %r', migration.__name__)
            m.run()

        log.info('Migrations complete')

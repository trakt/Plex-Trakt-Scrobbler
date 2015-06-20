from plugin.core.helpers.thread import module
from plugin.models.core import db
from plugin.modules.migrations.account import AccountMigration
from plugin.modules.migrations.preferences import PreferencesMigration
from plugin.modules.migrations.schema import SchemaMigration

import logging

log = logging.getLogger(__name__)


@module(start=True, priority=0, blocking=True)
class Migrations(object):
    migrations = [
        SchemaMigration,

        AccountMigration
    ]

    @classmethod
    def start(cls):
        # Connect to database, enable WAL
        db.connect()
        db.execute_sql('PRAGMA journal_mode=WAL;')

        # Run each migration
        for migration in cls.migrations:
            m = migration()

            log.info('Running migration: %r', migration.__name__)
            m.run()

        log.info('Migrations complete')

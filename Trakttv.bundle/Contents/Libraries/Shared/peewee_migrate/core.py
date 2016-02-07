from os import path as op, listdir as ls, makedirs as md
from re import compile as re
import sys
from shutil import copy
import logging
from playhouse.db_url import connect
from playhouse.migrate import SchemaMigrator
import datetime as dt
from .utils import exec_in

from peewee import SqliteDatabase, MySQLDatabase, PostgresqlDatabase, Proxy, Model, CharField

try:
    from playhouse.apsw_ext import DateTimeField
except ImportError:
    from peewee import DateTimeField


log = logging.getLogger(__name__)

MIGRATE_TEMPLATE = op.join(
    op.abspath(op.dirname(__file__)),
    'migration.tmpl'
)


class MigrationError(Exception):

    """ Presents an error during migration process. """


class Router(object):

    """ Control migrations. """

    filemask = re(r"[\d]{3}_[^\.]+\.py")
    proxy = Proxy()

    def __init__(self, migrate_dir, **options):

        if not op.exists(migrate_dir):
            log.warn('Migration directory: %s does not exists.', migrate_dir)
            md(migrate_dir)

        config = {}
        if op.exists(op.join(migrate_dir, 'conf.py')):
            with open(op.join(migrate_dir, 'conf.py')) as f:
                exec_in(f.read(), config, config)
            for key in config:
                if not key.startswith('_'):
                    options[key] = config[key]
        else:
            log.warn('Configuration file `conf.py` didnt found in migration directory')

        self.migrate_dir = migrate_dir

        self.db = options.get('DATABASE')
        if not isinstance(
                self.db, (SqliteDatabase, MySQLDatabase, PostgresqlDatabase)) and self.db:
            self.db = connect(self.db)

        try:
            assert self.db
            self.proxy.initialize(self.db)
            assert self.proxy.database
            MigrateHistory.create_table()
        except (AttributeError, AssertionError):
            log.error("Invalid database: %s", self.db)
            sys.exit(1)
        except Exception:
            pass

    @property
    def fs_migrations(self):
        files = [
            f[:-3] for f in ls(self.migrate_dir)
            if self.filemask.match(f)
        ]

        return sorted(files, key=lambda f: int(f.split('_')[0]))

    @property
    def db_migrations(self):
        return [mm.name for mm in MigrateHistory.select()]

    @property
    def diff(self):
        db = set(self.db_migrations)
        return [name for name in self.fs_migrations if name not in db]

    def create(self, name):
        """ Create a migration. """

        log.info('Create a migration "%s"', name)

        num = len(self.fs_migrations)
        prefix = '{:03}_'.format(num)
        name = prefix + name + '.py'
        copy(MIGRATE_TEMPLATE, op.join(self.migrate_dir, name))

        log.info('Migration has created %s', name)

    def run(self, name=None):
        """ Run migrations. """

        log.info('Running migrations...')

        migrator = Migrator(self.db)

        # Run migration by name
        if name:
            return self.run_one(name, migrator)

        # Report currently applied migrations
        db_migrations = self.db_migrations

        if db_migrations:
            log.info('Database has %d migrations applied:\n  %s', len(db_migrations), '\n  '.join(db_migrations))

        # Run migrations that haven't been applied yet
        diff = self.diff

        if diff:
            log.info('Applying %d database migrations:\n  %s', len(diff), '\n  '.join(diff))

            for name in diff:
                self.run_one(name, migrator)
        else:
            log.info('Nothing to migrate')

    def run_one(self, name, migrator):
        """ Run a migration. """

        log.info('Running migration "%s"...', name)

        try:
            migration = self._migration(name)

            with self.db.transaction():
                migrate = migration.get('migrate', lambda m: None)

                log.info('Start migration %s', name)
                migrate(migrator, self.db)

                MigrateHistory.create(name=name)
                log.info('Migrated %s', name)

        except Exception as exc:
            log.error(exc, exc_info=True)
            self.db.rollback()

    def validate(self):
        specification = {}

        log.info('Validating migrations...')

        # Retrieve current specification
        db_migrations = sorted(self.db_migrations, key=lambda f: int(f.split('_')[0]))
        current = None

        for name in db_migrations:
            # Load migration from file
            migration = self._migration(name)

            # Retrieve specification for migration
            spec = migration.get('SPEC')

            if spec is None:
                log.warn('Migration "%s" has no specification', name)
                continue

            # Update root specification
            specification.update(spec)

            # Validate migrations have been applied correctly
            log.debug('Validating migration schema: %r', name)

            if self._validate_schema(specification):
                current = name
            elif current:
                break

        log.info('Current migration: %r', current)

        # Check database schema matches applied migrations
        if db_migrations[-1] != current:
            log.warn('Database schema doesn\'t match applied migrations (current: %r, latest: %r)', current, db_migrations[-1])
            return False

        return True

    def _migration(self, name):
        with open(op.join(self.migrate_dir, name + '.py')) as f:
            code = f.read()

        scope = {}
        exec_in(code, scope)

        return scope

    def _table_schema(self, table):
        rows = self.db.execute_sql('PRAGMA table_info(\'%s\')' % table).fetchall()
        result = {}

        for _, name, data_type, not_null, _, primary_key in rows:
            parts = [data_type]

            if primary_key:
                parts.append('PRIMARY KEY')

            if not_null:
                parts.append('NOT NULL')

            result[name] = ' '.join(parts)

        return result

    def _validate_schema(self, spec):
        invalid = []

        for table, fields in spec.items():
            valid = True

            # Retrieve table schema
            schema = self._table_schema(table)
            pending = set(schema.keys())

            for name, definition in fields.items():
                # Ensure field exists
                if name not in schema:
                    log.debug(' - [%-24s] (%-22s) Field not in table', table, name)
                    valid = False
                    continue

                # Compare definition with table schema
                if definition != schema[name]:
                    log.debug(' - [%-24s] (%-22s) Definition mismatch (migration: %r, database: %r)', table, name, definition, schema[name])
                    valid = False

                # Mark field as completed
                pending.remove(name)

            # Ensure no fields have been skipped
            if pending:
                log.debug(' - [%-24s] Skipped %d field(s): %s', table, len(pending), ', '.join(pending))
                valid = False

            # Check table is valid
            if not valid:
                invalid.append(table)

        # Report validation results
        if invalid:
            log.debug(' - Detected %d/%d invalid table(s)', len(invalid), len(spec))
            return False

        log.debug(' - Verified %d table(s)', len(spec))
        return True


class MigrateHistory(Model):

    """ Presents the migrations in database. """

    name = CharField()
    migrated_at = DateTimeField(default=dt.datetime.utcnow)

    class Meta:
        database = Router.proxy


class Migrator(object):

    """ Provide migrations. """

    def __init__(self, db):
        self.db = db
        self.migrator = SchemaMigrator.from_database(self.db)

    def create_table(self, model):
        self.db.create_table(model)

    def create_tables(self, *models):
        self.db.create_tables(models)

    def drop_table(self, model):
        self.db.drop_table(model)

    def drop_tables(self, *models):
        self.db.drop_tables(models)

    def add_column(self, table, name, field):
        operation = self.migrator.add_column(table, name, field)
        return operation.run()

    def drop_column(self, table, name, field, cascade=True):
        operation = self.migrator.drop_column(table, name, field, cascade=cascade)
        return operation.run()

    def rename_column(self, table, old_name, new_name):
        operation = self.migrator.rename_column(table, old_name, new_name)
        return operation.run()

    def rename_table(self, old_name, new_name):
        operation = self.migrator.rename_table(old_name, new_name)
        return operation.run()

    def add_index(self, table, columns, unique=False):
        operation = self.migrator.add_index(table, columns, unique=unique)
        return operation.run()

    def drop_index(self, table, index_name):
        operation = self.migrator.drop_index(table, index_name)
        return operation.run()

    def add_not_null(self, table, column):
        operation = self.migrator.add_not_null(table, column)
        return operation.run()

    def drop_not_null(self, table, column):
        operation = self.migrator.drop_not_null(table, column)
        return operation.run()


# pylama:ignore=R0201,E0602,E0611,W0703,E1103

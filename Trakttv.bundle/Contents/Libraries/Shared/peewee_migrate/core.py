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
            log.warn('Migration directory: %s does not exist', migrate_dir)
            md(migrate_dir)

        config = {}
        if op.exists(op.join(migrate_dir, 'conf.py')):
            with open(op.join(migrate_dir, 'conf.py')) as f:
                exec_in(f.read(), config, config)
            for key in config:
                if not key.startswith('_'):
                    options[key] = config[key]
        else:
            log.info('Configuration file `conf.py` wasn\'t found in the migration directory')

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

        try:
            migration = self._migration(name)
            migrate = migration.get('migrate', lambda m: None)

            with self.db.transaction():
                log.info('Running migration "%s"...', name)
                migrate(migrator, self.db)

                MigrateHistory.create(name=name)
                log.info('Migrated "%s"', name)

        except Exception as exc:
            log.error(exc, exc_info=True)
            self.db.rollback()

    def validate(self):
        # Retrieve database migrations
        db_migrations = self.db_migrations

        if not db_migrations:
            # No migrations applied to database yet
            return True

        # Match specification against migration
        current = self.match(db_migrations)

        # Check database schema matches applied migrations
        if db_migrations[-1] != current:
            log.warn('Database schema doesn\'t match applied migrations (current: %r, latest: %r)', current, db_migrations[-1])
            return False

        return True

    def match(self, migrations=None, check_all=False):
        # Retrieve current specification
        if migrations is None:
            migrations = self.db_migrations

        if not migrations:
            return None

        # Sort migrations by index
        migrations = sorted(migrations, key=lambda f: int(f.split('_')[0]))

        # Build complete migration specifications
        migration_specs = []
        specification = {}

        for name in migrations:
            # Load migration from file
            migration = self._migration(name)

            if not migration:
                break

            # Retrieve specification for migration
            spec = migration.get('SPEC')

            if spec is None:
                log.warn('Migration "%s" has no specification', name)
                continue

            # Update root specification
            specification.update(spec)

            # Store specification
            migration_specs.append((name, specification.copy()))

        # Validate migrations (latest migrations first)
        for name, spec in reversed(migration_specs):
            # Validate migrations have been applied correctly
            log.debug('Validating migration "%s"...', name)

            if self._validate_schema(spec):
                return name
            elif not check_all:
                break

        return None

    def _migration(self, name):
        path = op.join(self.migrate_dir, name + '.py')

        # Ensure migration exists
        if not op.exists(path):
            return None

        # Read migration module
        with open(path) as f:
            code = f.read()

        scope = {}
        exec_in(code, scope)

        return scope

    def _tables(self):
        rows = self.db.execute_sql(
            'SELECT name FROM sqlite_master WHERE type=\'table\';'
        ).fetchall()

        return [
            name for (name,) in rows
        ]

    def _table_schema(self, table):
        rows = self.db.execute_sql(
            'PRAGMA table_info(\'%s\')' % table
        ).fetchall()

        # Build list of fields from table information
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
        # Retrieve available tables from database
        tables = set(self._tables())
        tables.remove('migratehistory')  # Ignore migration history table

        pending_tables = tables.copy()

        # Iterate over table specifications
        invalid = []

        for table, fields in spec.items():
            # Ensure table exists
            if table not in pending_tables:
                log.warn('[%-24s] Table doesn\'t exist', table)
                invalid.append(table)
                continue

            # Retrieve table schema
            schema = self._table_schema(table)
            pending_fields = set(schema.keys())
            valid = True

            for name, definition in fields.items():
                # Ensure field exists
                if name not in schema:
                    log.warn('[%-24s] (%-22s) Field not in table', table, name)
                    valid = False
                    continue

                # Compare definition with table schema
                if definition != schema[name]:
                    log.warn('[%-24s] (%-22s) Definition mismatch (migration: %r, database: %r)', table, name, definition, schema[name])
                    valid = False

                # Mark field as completed
                pending_fields.remove(name)

            # Ensure no fields have been skipped
            if pending_fields:
                log.warn('[%-24s] Skipped %d field(s): %s', table, len(pending_fields), ', '.join(pending_fields))
                valid = False

            # Check table is valid
            if not valid:
                invalid.append(table)

            # Mark table as completed
            pending_tables.remove(table)

        # Report validation results
        if invalid:
            log.warn('Errors detected on %d/%d table(s)', len(invalid), len(spec))
            return False

        if len(pending_tables) > 0:
            log.warn('Skipped %d table(s): %s', len(pending_tables), ', '.join(pending_tables))
            return False

        log.info('Validated %d table(s)', len(spec))
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
        model.create_table(db=self.db)

    def create_tables(self, *models):
        for model in models:
            self.create_table(model)

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

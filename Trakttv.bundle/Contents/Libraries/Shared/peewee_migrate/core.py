from os import path as op, listdir as ls, makedirs as md
from re import compile as re
import sys
from shutil import copy
import logging
from playhouse.db_url import connect
from playhouse.migrate import SchemaMigrator
import datetime as dt
from .utils import exec_in

from peewee import * # noqa


LOGGER = logging.getLogger()
LOGGER.addHandler(logging.StreamHandler())
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

        LOGGER.setLevel(options.get('LOGGING', 'WARNING'))

        if not op.exists(migrate_dir):
            LOGGER.warn('Migration directory: %s does not exists.', migrate_dir)
            md(migrate_dir)

        config = {}
        if op.exists(op.join(migrate_dir, 'conf.py')):
            with open(op.join(migrate_dir, 'conf.py')) as f:
                exec_in(f.read(), config, config)
            for key in config:
                if not key.startswith('_'):
                    options[key] = config[key]
        else:
            LOGGER.warn('Configuration file `conf.py` didnt found in migration directory')

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
            LOGGER.error("Invalid database: %s", self.db)
            sys.exit(1)
        except Exception:
            pass

    @property
    def fs_migrations(self):
        return sorted(''.join(f[:-3]) for f in ls(self.migrate_dir) if self.filemask.match(f))

    @property
    def db_migrations(self):
        return [mm.name for mm in MigrateHistory.select()]

    @property
    def diff(self):
        db = set(self.db_migrations)
        return [name for name in self.fs_migrations if name not in db]

    def run(self, name=None):
        """ Run migrations. """

        LOGGER.info('Start migrations')

        migrator = Migrator(self.db)
        if name:
            return self.run_one(name, migrator)

        diff = self.diff
        for name in diff:
            self.run_one(name, migrator)

        if not diff:
            LOGGER.info('Nothing to migrate')

    def run_one(self, name, migrator):
        """ Run a migration. """

        LOGGER.info('Run "%s"', name)

        try:
            with open(op.join(self.migrate_dir, name + '.py')) as f:
                with self.db.transaction():
                    code = f.read()
                    scope = {}
                    exec_in(code, scope)
                    migrate = scope.get('migrate', lambda m: None)
                    logging.info('Start migration %s', name)
                    migrate(migrator, self.db)
                    MigrateHistory.create(name=name)
                    logging.info('Migrated %s', name)

        except Exception as exc:
            self.db.rollback()
            LOGGER.error(exc)

    def create(self, name):
        """ Create a migration. """

        LOGGER.info('Create a migration "%s"', name)

        num = len(self.fs_migrations)
        prefix = '{:03}_'.format(num)
        name = prefix + name + '.py'
        copy(MIGRATE_TEMPLATE, op.join(self.migrate_dir, name))

        LOGGER.info('Migration has created %s', name)


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

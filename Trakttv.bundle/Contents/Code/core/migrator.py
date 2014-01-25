from core.logger import Logger
from core.plugin import PLUGIN_VERSION_BASE
import shutil
import os

log = Logger('core.migrator')


class Migrator(object):
    migrations = []

    @classmethod
    def register(cls, migration):
        cls.migrations.append(migration())

    @classmethod
    def run(cls):
        for migration in cls.migrations:
            log.debug('Running migration %s', migration)
            migration.run()


class Migration(object):
    @property
    def code_path(self):
        return Core.code_path


class SyncMigration(Migration):
    def run(self):
        if PLUGIN_VERSION_BASE >= (0, 8):
            self.upgrade()
        else:
            self.downgrade()

    def upgrade(self):
        sync_path = os.path.join(self.code_path, 'sync.py')

        if os.path.exists(sync_path) and os.path.isfile(sync_path):
            log.debug('Removing "sync.py" file')
            os.remove(sync_path)

    def downgrade(self):
        sync_path = os.path.join(self.code_path, 'sync')

        if os.path.exists(sync_path) and os.path.isdir(sync_path):
            log.debug('Removing "sync" folder')
            shutil.rmtree(sync_path)

Migrator.register(SyncMigration)
Migrator.run()

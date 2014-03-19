from core.helpers import all
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

    @staticmethod
    def delete_file(path, conditions=None):
        if not all([c(path) for c in conditions]):
            return False

        os.remove(path)

    @staticmethod
    def delete_directory(path, conditions=None):
        if not all([c(path) for c in conditions]):
            return False

        shutil.rmtree(path)


class Clean(Migration):
    tasks_upgrade = [
        (
            'delete_file', [
                'data/dict_object.py',
                'plex/media_server.py',
                'sync.py'
            ], os.path.isfile
        )
    ]

    def run(self):
        if PLUGIN_VERSION_BASE >= (0, 8):
            self.upgrade()

    def upgrade(self):
        self.execute(self.tasks_upgrade, 'upgrade')

    def execute(self, tasks, name):
        for action, paths, conditions in tasks:
            if type(paths) is not list:
                paths = [paths]

            if type(conditions) is not list:
                conditions = [conditions]

            if not hasattr(self, action):
                log.warn('Unknown migration action "%s"', action)
                continue

            m = getattr(self, action)

            for path in paths:
                log.debug('(%s) %s: "%s"', name, action, path)

                if m(os.path.join(self.code_path, path), conditions):
                    log.debug('(%s) %s: "%s" - finished', name, action, path)


Migrator.register(Clean)
Migrator.run()

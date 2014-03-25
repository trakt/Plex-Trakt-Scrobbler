from core.helpers import all
from core.logger import Logger
from core.plugin import PLUGIN_VERSION_BASE
from lxml import etree
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

    @property
    def plex_path(self):
        return os.path.abspath(os.path.join(self.code_path, '..', '..', '..', '..'))

    @property
    def preferences_path(self):
        return os.path.join(self.plex_path, 'Plug-in Support', 'Preferences', 'com.plexapp.plugins.trakttv.xml')

    @staticmethod
    def delete_file(path, conditions=None):
        if not all([c(path) for c in conditions]):
            return False

        os.remove(path)
        return True

    @staticmethod
    def delete_directory(path, conditions=None):
        if not all([c(path) for c in conditions]):
            return False

        shutil.rmtree(path)
        return True


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


class ForceLegacy(Migration):
    """Migrates the 'force_legacy' option to the 'activity_mode' option."""

    def run(self):
        self.upgrade()

    def upgrade(self):
        if not os.path.exists(self.preferences_path):
            log.warn('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
            return

        data = Core.storage.load(self.preferences_path)
        doc = etree.fromstring(data)

        # Read 'force_legacy' option from raw preferences
        force_legacy = doc.find('force_legacy')

        if force_legacy is None:
            return

        force_legacy = (force_legacy.text or '').lower() == "true"

        if not force_legacy:
            return

        # Read 'activity_mode' option from raw preferences
        activity_mode_node = doc.find('activity_mode')
        activity_mode = None

        if activity_mode_node is not None:
            activity_mode = activity_mode_node.text

        # Activity mode has already been set, not changing it
        if activity_mode is not None:
            return

        # Ensure 'activity_mode' node exists
        if activity_mode_node is None:
            activity_mode_node = etree.SubElement(doc, "activity_mode")

        # Set mode to 1 Legacy (Logging)
        activity_mode_node.text = '1'

        log.debug('Activity mode updated to 1 "Legacy (Logging)"')

        # Store back new preferences
        Core.storage.save(self.preferences_path, etree.tostring(doc, pretty_print=True))


Migrator.register(Clean)
Migrator.register(ForceLegacy)
Migrator.run()

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
    def lib_path(self):
        return os.path.join(self.code_path, '..', 'Libraries')

    @property
    def plex_path(self):
        return os.path.abspath(os.path.join(self.code_path, '..', '..', '..', '..'))

    @property
    def preferences_path(self):
        return os.path.join(self.plex_path, 'Plug-in Support', 'Preferences', 'com.plexapp.plugins.trakttv.xml')

    def get_preferences(self):
        if not os.path.exists(self.preferences_path):
            log.warn('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
            return {}

        data = Core.storage.load(self.preferences_path)
        doc = etree.fromstring(data)

        return dict([(elem.tag, elem.text) for elem in doc])

    def set_preferences(self, changes):
        if not os.path.exists(self.preferences_path):
            log.warn('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
            return False

        data = Core.storage.load(self.preferences_path)
        doc = etree.fromstring(data)

        for key, value in changes.items():
            elem = doc.find(key)

            # Ensure node exists
            if elem is None:
                elem = etree.SubElement(doc, key)

            # Update node value, ensure it is a string
            elem.text = str(value)

            log.trace('Updated preference with key "%s" to value %s', key, repr(value))

        # Write back new preferences
        Core.storage.save(self.preferences_path, etree.tostring(doc, pretty_print=True))

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
    tasks_code = [
        (
            'delete_file', [
                'core/trakt.py',
                'core/trakt_objects.py',
                'data/dict_object.py',
                'plex/media_server.py',
                'sync.py'
            ], os.path.isfile
        )
    ]

    tasks_lib = [
        (
            'delete_file', [
                'Shared/asio.py',                 'Shared/asio.pyc',
                'Shared/asio_base.py',            'Shared/asio_base.pyc',
                'Shared/asio_posix.py',           'Shared/asio_posix.pyc',
                'Shared/asio_windows.py',         'Shared/asio_windows.pyc',
                'Shared/asio_windows_interop.py', 'Shared/asio_windows_interop.pyc'
            ], os.path.isfile
        )
    ]

    def run(self):
        if PLUGIN_VERSION_BASE >= (0, 8):
            self.upgrade()

    def upgrade(self):
        self.execute(self.tasks_code, 'upgrade', self.code_path)
        self.execute(self.tasks_lib, 'upgrade', self.lib_path)

    def execute(self, tasks, name, base_path):
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
                path = os.path.join(base_path, path)
                path = os.path.abspath(path)

                log.debug('(%s) %s: "%s"', name, action, path)

                if m(path, conditions):
                    log.debug('(%s) %s: "%s" - finished', name, action, path)


class ForceLegacy(Migration):
    """Migrates the 'force_legacy' option to the 'activity_mode' option."""

    def run(self):
        self.upgrade()

    def upgrade(self):
        if not os.path.exists(self.preferences_path):
            log.warn('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
            return

        preferences = self.get_preferences()

        # Read 'force_legacy' option from raw preferences
        force_legacy = preferences.get('force_legacy')

        if force_legacy is None:
            return

        force_legacy = force_legacy.lower() == "true"

        if not force_legacy:
            return

        # Read 'activity_mode' option from raw preferences
        activity_mode = preferences.get('activity_mode')

        # Activity mode has already been set, not changing it
        if activity_mode is not None:
            return

        self.set_preferences({
            'activity_mode': '1'
        })


class SelectiveSync(Migration):
    """Migrates the syncing task bool options to selective synchronize/push/pull enums"""

    option_keys = [
        'sync_watched',
        'sync_ratings',
        'sync_collection'
    ]

    value_map = {
        'false': '0',
        'true': '1',
    }

    def run(self):
        self.upgrade()

    def upgrade(self):
        preferences = self.get_preferences()

        # Filter to only relative preferences
        preferences = dict([
            (key, value)
            for key, value in preferences.items()
            if key in self.option_keys
        ])

        changes = {}

        for key, value in preferences.items():
            if value not in self.value_map:
                continue

            changes[key] = self.value_map[value]

        if not changes:
            return

        log.debug('Updating preferences with changes: %s', changes)
        self.set_preferences(changes)


Migrator.register(Clean)
Migrator.register(ForceLegacy)
Migrator.register(SelectiveSync)
Migrator.run()

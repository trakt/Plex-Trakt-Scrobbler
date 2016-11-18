from plugin.core.constants import PLUGIN_VERSION_BASE
from plugin.core.helpers.variable import all

from lxml import etree
import shutil
import os


class FSMigrator(object):
    migrations = []

    @classmethod
    def register(cls, migration):
        cls.migrations.append(migration())

    @classmethod
    def run(cls):
        for migration in cls.migrations:
            Log.Debug('Running migration: %s', migration)
            migration.run()


class Migration(object):
    @property
    def code_path(self):
        return Core.code_path

    @property
    def lib_path(self):
        return os.path.join(self.code_path, '..', 'Libraries')

    @property
    def tests_path(self):
        return os.path.join(self.code_path, '..', 'Tests')

    @property
    def plex_path(self):
        return os.path.abspath(os.path.join(self.code_path, '..', '..', '..', '..'))

    @property
    def preferences_path(self):
        return os.path.join(self.plex_path, 'Plug-in Support', 'Preferences', 'com.plexapp.plugins.trakttv.xml')

    def get_preferences(self):
        if not os.path.exists(self.preferences_path):
            Log.Error('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
            return {}

        data = Core.storage.load(self.preferences_path)
        doc = etree.fromstring(data)

        return dict([(elem.tag, elem.text) for elem in doc])

    def set_preferences(self, changes):
        if not os.path.exists(self.preferences_path):
            Log.Error('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
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

            Log.Debug('Updated preference with key "%s" to value %s', key, repr(value))

        # Write back new preferences
        Core.storage.save(self.preferences_path, etree.tostring(doc, pretty_print=True))

    @staticmethod
    def delete_file(path, conditions=None):
        if not all([c(path) for c in conditions]):
            return False

        try:
            os.remove(path)
            return True
        except Exception as ex:
            Log.Warn('Unable to remove file %r - %s', path, ex, exc_info=True)

        return False

    @staticmethod
    def delete_directory(path, conditions=None):
        if not all([c(path) for c in conditions]):
            return False

        try:
            shutil.rmtree(path)
            return True
        except Exception as ex:
            Log.Warn('Unable to remove directory %r - %s', path, ex, exc_info=True)

        return False


class Clean(Migration):
    tasks_code = [
        (
            'delete_file', [
                # /core
                'core/action.py',
                'core/cache.py',
                'core/configuration.py',
                'core/environment.py',
                'core/eventing.py',
                'core/localization.py',
                'core/logging_handler.py',
                'core/logging_reporter.py',
                'core/method_manager.py',
                'core/migrator.py',
                'core/model.py',
                'core/network.py',
                'core/numeric.py',
                'core/plugin.py',
                'core/task.py',
                'core/trakt.py',
                'core/trakt_objects.py',

                # /interface
                'interface/main_menu.py',
                'interface/sync_menu.py',

                # /
                'libraries.py',
                'sync.py'
            ], os.path.isfile
        ),
        (
            'delete_directory', [
                'data',
                'plex',
                'pts',
                'sync'
            ], os.path.isdir
        )
    ]

    tasks_lib = [
        (
            'delete_file', [
                # plugin
                'Shared/plugin/api/account.py',
                'Shared/plugin/core/event.py',
                'Shared/plugin/core/io.py',
                'Shared/plugin/core/jsonw.py',
                'Shared/plugin/core/libraries/main.py',
                'Shared/plugin/core/libraries/tests/pyopenssl_.py',
                'Shared/plugin/core/session_status.py',
                'Shared/plugin/models/core/exceptions.py',
                'Shared/plugin/modules/base.py',
                'Shared/plugin/modules/manager.py',
                'Shared/plugin/preferences/options/core/base.py',
                'Shared/plugin/sync/modes/core/base.py',
                'Shared/plugin/sync/modes/fast_pull.py',
                'Shared/plugin/sync/modes/pull.py',
                'Shared/plugin/sync/modes/push.py',

                # native
                'FreeBSD/i386/apsw.so',
                'FreeBSD/i386/llist.so',

                'FreeBSD/i386/ucs2/apsw.dependencies',
                'FreeBSD/i386/ucs2/apsw.file',
                'FreeBSD/i386/ucs2/llist.dependencies',
                'FreeBSD/i386/ucs2/llist.file',
                'FreeBSD/i386/ucs4/apsw.dependencies',
                'FreeBSD/i386/ucs4/apsw.file',
                'FreeBSD/i386/ucs4/llist.dependencies',
                'FreeBSD/i386/ucs4/llist.file',

                'FreeBSD/x86_64/ucs2/apsw.dependencies',
                'FreeBSD/x86_64/ucs2/apsw.file',
                'FreeBSD/x86_64/ucs2/llist.dependencies',
                'FreeBSD/x86_64/ucs2/llist.file',
                'FreeBSD/x86_64/ucs4/apsw.dependencies',
                'FreeBSD/x86_64/ucs4/apsw.file',
                'FreeBSD/x86_64/ucs4/llist.dependencies',
                'FreeBSD/x86_64/ucs4/llist.file',

                'Windows/i386/apsw.pyd',
                'Windows/i386/llist.pyd',

                'Linux/i386/apsw.so',
                'Linux/i386/llist.so',
                'Linux/x86_64/apsw.so',
                'Linux/x86_64/llist.so',

                'Linux/armv6_hf/ucs4/apsw.dependencies',
                'Linux/armv6_hf/ucs4/apsw.file',
                'Linux/armv6_hf/ucs4/apsw.header',
                'Linux/armv6_hf/ucs4/llist.dependencies',
                'Linux/armv6_hf/ucs4/llist.file',
                'Linux/armv6_hf/ucs4/llist.header',

                'Linux/armv7_hf/ucs4/apsw.dependencies',
                'Linux/armv7_hf/ucs4/apsw.file',
                'Linux/armv7_hf/ucs4/apsw.header',
                'Linux/armv7_hf/ucs4/llist.dependencies',
                'Linux/armv7_hf/ucs4/llist.file',
                'Linux/armv7_hf/ucs4/llist.header',

                'Linux/i386/ucs2/apsw.dependencies',
                'Linux/i386/ucs2/apsw.file',
                'Linux/i386/ucs2/llist.dependencies',
                'Linux/i386/ucs2/llist.file',
                'Linux/i386/ucs4/apsw.dependencies',
                'Linux/i386/ucs4/apsw.file',
                'Linux/i386/ucs4/llist.dependencies',
                'Linux/i386/ucs4/llist.file',

                'Linux/x86_64/ucs2/apsw.dependencies',
                'Linux/x86_64/ucs2/apsw.file',
                'Linux/x86_64/ucs2/llist.dependencies',
                'Linux/x86_64/ucs2/llist.file',
                'Linux/x86_64/ucs4/apsw.dependencies',
                'Linux/x86_64/ucs4/apsw.file',
                'Linux/x86_64/ucs4/llist.dependencies',
                'Linux/x86_64/ucs4/llist.file',

                'MacOSX/i386/ucs2/apsw.dependencies',
                'MacOSX/i386/ucs2/apsw.file',
                'MacOSX/i386/ucs2/llist.dependencies',
                'MacOSX/i386/ucs2/llist.file',
                'MacOSX/i386/ucs4/apsw.dependencies',
                'MacOSX/i386/ucs4/apsw.file',
                'MacOSX/i386/ucs4/llist.dependencies',
                'MacOSX/i386/ucs4/llist.file',

                'MacOSX/x86_64/ucs2/apsw.dependencies',
                'MacOSX/x86_64/ucs2/apsw.file',
                'MacOSX/x86_64/ucs2/llist.dependencies',
                'MacOSX/x86_64/ucs2/llist.file',
                'MacOSX/x86_64/ucs4/apsw.dependencies',
                'MacOSX/x86_64/ucs4/apsw.file',
                'MacOSX/x86_64/ucs4/llist.dependencies',
                'MacOSX/x86_64/ucs4/llist.file',

                'Windows/i386/ucs2/apsw.pyd',
                'Windows/i386/ucs2/llist.pyd',

                # asio
                'Shared/asio.py',
                'Shared/asio_base.py',
                'Shared/asio_posix.py',
                'Shared/asio_windows.py',
                'Shared/asio_windows_interop.py',

                # concurrent
                'Shared/concurrent/futures/_compat.py',

                # msgpack
                'Shared/msgpack/_packer.pyx',
                'Shared/msgpack/_unpacker.pyx',
                'Shared/msgpack/pack.h',
                'Shared/msgpack/pack_template.h',
                'Shared/msgpack/sysdep.h',
                'Shared/msgpack/unpack.h',
                'Shared/msgpack/unpack_define.h',
                'Shared/msgpack/unpack_template.h',

                # playhouse
                'Shared/playhouse/pskel',

                # plex.py
                'Shared/plex/core/compat.py',
                'Shared/plex/core/event.py',
                'Shared/plex/interfaces/library.py',
                'Shared/plex/interfaces/plugin.py',

                # plex.metadata.py
                'Shared/plex_metadata/core/cache.py',

                # requests
                'Shared/requests/packages/urllib3/util.py',
                'Shared/requests/packages/README.rst',

                # trakt.py
                'Shared/trakt/core/context.py',
                'Shared/trakt/interfaces/base/media.py',
                'Shared/trakt/interfaces/account.py',
                'Shared/trakt/interfaces/rate.py',
                'Shared/trakt/interfaces/sync/base.py',
                'Shared/trakt/media_mapper.py',
                'Shared/trakt/objects.py',
                'Shared/trakt/objects/list.py',
                'Shared/trakt/request.py',

                # tzlocal
                'Shared/tzlocal/tests.py',

                # websocket
                'Shared/websocket.py'
            ], os.path.isfile
        ),
        (
            'delete_directory', [
                # plugin
                'Shared/plugin/core/collections',
                'Shared/plugin/data',
                'Shared/plugin/modules/backup',

                # native
                'MacOSX/universal',

                # pytz
                'Shared/pytz/tests',

                # shove
                'Shared/shove',

                # stuf
                'Shared/stuf',

                # trakt.py
                'Shared/trakt/interfaces/movie',
                'Shared/trakt/interfaces/show',
                'Shared/trakt/interfaces/user',

                # tzlocal
                'Shared/tzlocal/test_data'
            ], os.path.isdir
        )
    ]

    tasks_tests = [
        (
            'delete_file', [
            ], os.path.isfile
        ),
        (
            'delete_directory', [
                'tests/core/mock',
            ], os.path.isdir
        )
    ]

    def run(self):
        if PLUGIN_VERSION_BASE >= (0, 8):
            self.upgrade()

    def upgrade(self):
        self.execute(self.tasks_code, 'upgrade', self.code_path)
        self.execute(self.tasks_lib, 'upgrade', self.lib_path)
        self.execute(self.tasks_tests, 'upgrade', self.tests_path)

    def execute(self, tasks, name, base_path):
        for action, paths, conditions in tasks:
            if type(paths) is not list:
                paths = [paths]

            if type(conditions) is not list:
                conditions = [conditions]

            if not hasattr(self, action):
                Log.Error('Unknown migration action "%s"', action)
                continue

            m = getattr(self, action)

            for path in paths:
                path = os.path.join(base_path, path)
                path = os.path.abspath(path)

                # Remove file
                if m(path, conditions):
                    Log.Info('(%s) %s: "%s"', name, action, path)

                # Remove .pyc files as-well
                if path.endswith('.py') and m(path + 'c', conditions):
                    Log.Info('(%s) %s: "%s"', name, action, path + 'c')


class ForceLegacy(Migration):
    """Migrates the 'force_legacy' option to the 'activity_mode' option."""

    def run(self):
        self.upgrade()

    def upgrade(self):
        if not os.path.exists(self.preferences_path):
            Log.Error('Unable to find preferences file at "%s", unable to run migration', self.preferences_path)
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

        Log.Debug('Updating preferences with changes: %s', changes)
        self.set_preferences(changes)


FSMigrator.register(Clean)
FSMigrator.register(ForceLegacy)
FSMigrator.register(SelectiveSync)

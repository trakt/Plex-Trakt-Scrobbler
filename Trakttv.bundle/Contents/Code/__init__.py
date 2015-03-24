# ------------------------------------------------
# IMPORTANT
# Configure environment module before we import other modules (that could depend on it)
# ------------------------------------------------
from plugin.core.environment import Environment

# Configure environment
Environment.setup(Core, Dict, Prefs)
# ------------------------------------------------

# ------------------------------------------------
# IMPORTANT
# These modules need to be loaded here first
# ------------------------------------------------
import core
import data
import sync
import interface
# ------------------------------------------------

# Check "apsw" availability, log any errors
try:
    import apsw

    Log.Debug('apsw: %r, sqlite: %r', apsw.apswversion(), apsw.SQLITE_VERSION_NUMBER)
except Exception, ex:
    Log.Error('Unable to import "apsw": %s', ex)

from core.cache import CacheManager
from core.configuration import Configuration
from core.header import Header
from core.logger import Logger
from core.logging_reporter import RAVEN
from core.helpers import spawn, get_pref, schedule, get_class_name, md5
from core.plugin import ART, NAME, ICON
from core.update_checker import UpdateChecker
from interface.main_menu import MainMenu
from plugin.core.constants import PLUGIN_VERSION, PLUGIN_IDENTIFIER
from plugin.core.helpers.thread import module_start
from plugin.modules.core.manager import ModuleManager
from sync.sync_manager import SyncManager

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata, Matcher
from requests.packages.urllib3.util import Retry
from trakt import Trakt, ClientError
import os


log = Logger()


class Main(object):
    modules = [
        Activity,

        # core
        UpdateChecker(),

        # sync
        SyncManager
    ]

    def __init__(self):
        Header.show(self)
        Main.update_config()

        self.init_trakt()
        self.init_plex()
        self.init()

        ModuleManager.initialize()

        # Initialize sentry error reporting
        self.init_raven()

    def init(self):
        names = []

        # Initialize modules
        for module in self.modules:
            names.append(get_class_name(module))

            if hasattr(module, 'initialize'):
                module.initialize()

        log.info('Initialized %s modules: %s', len(names), ', '.join(names))

    @classmethod
    def init_raven(cls):
        # Retrieve server details
        server = Plex.detail()

        if not server:
            return

        # Set client name to a hash of `machine_identifier`
        RAVEN.name = md5(server.machine_identifier)

        RAVEN.tags.update({
            'server.version': server.version
        })

    @staticmethod
    def init_plex():
        # plex.py
        Plex.configuration.defaults.authentication(
            os.environ.get('PLEXTOKEN')
        )

        # plex.activity.py
        path = os.path.join(Core.log.handlers[1].baseFilename, '..', '..', 'Plex Media Server.log')
        path = os.path.abspath(path)

        Activity['logging'].add_hint(path)

        # plex.metadata.py
        Metadata.configure(
            cache=CacheManager.get('metadata'),
            client=Plex.client
        )

    @staticmethod
    def init_trakt():
        # Client
        Trakt.configuration.defaults.client(
            id='c9ccd3684988a7862a8542ae0000535e0fbd2d1c0ca35583af7ea4e784650a61'
        )

        # Application
        Trakt.configuration.defaults.app(
            name='trakt (for Plex)',
            version=PLUGIN_VERSION
        )

        # Setup request retrying
        Trakt.http.adapter_kwargs = {'max_retries': Retry(total=3, read=0)}
        Trakt.http.rebuild()

    @classmethod
    def update_config(cls, valid=None):
        preferences = Dict['preferences'] or {}

        # If no validation provided, use last stored result or assume true
        if valid is None:
            valid = preferences.get('valid', True)

        preferences['valid'] = valid

        Configuration.process(preferences)

        # Ensure preferences dictionary is stored
        Dict['preferences'] = preferences
        Dict.Save()

        # Update plex.metadata.py `Matcher` preferences
        Matcher.set_caper(preferences['matcher'] == 'plex_extended')
        Matcher.set_extend(preferences['matcher'] == 'plex_extended')

        log.info('Preferences updated %s', preferences)
        # TODO EventManager.fire('preferences.updated', preferences)

    def start(self):
        # Check for authentication token
        log.info('X-Plex-Token: %s', 'available' if os.environ.get('PLEXTOKEN') else 'unavailable')

        # Start new-style modules
        module_start()

        # Start modules
        names = []

        for module in self.modules:
            if not hasattr(module, 'start'):
                continue

            names.append(get_class_name(module))

            module.start()

        log.info('Started %s modules: %s', len(names), ', '.join(names))

        ModuleManager.start()


def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    main = Main()
    main.start()


def ValidatePrefs():
    last_activity_mode = get_pref('activity_mode')

    # Restart if activity_mode has changed
    if Prefs['activity_mode'] != last_activity_mode:
        log.info('Activity mode has changed, restarting plugin...')
        # TODO this can cause the preferences dialog to get stuck on "saving"
        #  - might need to delay this for a few seconds to avoid this.
        spawn(lambda: Plex[':/plugins'].restart(PLUGIN_IDENTIFIER))

    return MessageContainer(
        "Success",
        "Success"
    )

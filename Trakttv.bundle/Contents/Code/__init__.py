# ------------------------------------------------
# IMPORTANT
# Configure environment module before we import other modules (that could depend on it)
# ------------------------------------------------
from plugin.core.environment import Environment

# Configure environment
Environment.setup(Core)
# ------------------------------------------------

# ------------------------------------------------
# IMPORTANT
# These modules need to be loaded here first
# ------------------------------------------------
import core
import data
import pts
import sync
import interface
# ------------------------------------------------


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
from plugin.modules.manager import ModuleManager
from pts.action_manager import ActionManager
from pts.scrobbler import Scrobbler
from pts.session_manager import SessionManager
from sync.sync_manager import SyncManager

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata
from trakt import Trakt, ClientError
import hashlib
import logging
import os


log = Logger()


class Main(object):
    modules = [
        Activity,

        # core
        UpdateChecker(),

        # pts
        ActionManager,
        Scrobbler,
        SessionManager(),

        # sync
        SyncManager,
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

        log.info('Preferences updated %s', preferences)
        # TODO EventManager.fire('preferences.updated', preferences)

    @classmethod
    def authenticate(cls, retry_interval=30):
        if not Prefs['username'] or not Prefs['password']:
            log.warn('Authentication failed, username or password field empty')

            cls.update_config(False)
            return False

        # Clear authentication details if username has changed
        if Dict['trakt.token'] and Dict['trakt.username'] != Prefs['username']:
            # Reset authentication details
            Dict['trakt.username'] = None
            Dict['trakt.token'] = None

            log.info('Authentication cleared, username was changed')

        # Authentication
        retry = False

        if not Dict['trakt.token']:
            # Authenticate with trakt.tv (no token has previously been stored)
            with Trakt.configuration.http(retry=True):
                try:
                    Dict['trakt.token'] = Trakt['auth'].login(
                        Prefs['username'],
                        Prefs['password'],
                        exceptions=True
                    )

                    Dict['trakt.username'] = Prefs['username']
                except ClientError, ex:
                    log.warn('Authentication failed: %s', ex, exc_info=True)
                    Dict['trakt.token'] = None

                    # Client error (invalid username or password), don't retry the request
                    retry = False
                except Exception, ex:
                    log.error('Authentication failed: %s', ex, exc_info=True)
                    Dict['trakt.token'] = None

                    # Server error, retry the request
                    retry = True

            Dict.Save()

        # Update trakt client configuration
        Trakt.configuration.defaults.auth(
            Dict['trakt.username'],
            Dict['trakt.token']
        )

        # TODO actually test trakt.tv authentication
        success = bool(Dict['trakt.token'])

        if not success:
            # status - False = invalid credentials, None = request failed
            if retry:
                # Increase retry interval each time to a maximum of 30 minutes
                if retry_interval < 60 * 30:
                    retry_interval = int(retry_interval * 1.3)

                # Ensure we never go over 30 minutes
                if retry_interval > 60 * 30:
                    retry_interval = 60 * 30

                log.warn('Unable to authentication with trakt.tv, will try again in %s seconds', retry_interval)
                schedule(cls.authenticate, retry_interval, retry_interval)
            else:
                log.warn('Authentication failed, username or password is incorrect')

            Main.update_config(False)
            return False

        log.info('Authentication successful')

        Main.update_config(True)
        return True

    def start(self):
        # Check for authentication token
        log.info('X-Plex-Token: %s', 'available' if os.environ.get('PLEXTOKEN') else 'unavailable')

        # Validate username/password
        spawn(self.authenticate)

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

    if Main.authenticate():
        message = MessageContainer(
            "Success",
            "Authentication successful"
        )
    else:
        message = MessageContainer(
            "Error",
            "Authentication failed, incorrect username or password"
        )

    # Restart if activity_mode has changed
    if Prefs['activity_mode'] != last_activity_mode:
        log.info('Activity mode has changed, restarting plugin...')
        # TODO this can cause the preferences dialog to get stuck on "saving"
        #  - might need to delay this for a few seconds to avoid this.
        spawn(lambda: Plex[':/plugins'].restart(PLUGIN_IDENTIFIER))

    return message

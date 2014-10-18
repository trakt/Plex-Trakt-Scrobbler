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
from core.helpers import spawn, get_pref, schedule, get_class_name
from core.plugin import ART, NAME, ICON, PLUGIN_VERSION, PLUGIN_IDENTIFIER
from core.update_checker import UpdateChecker
from interface.main_menu import MainMenu
from plugin.modules.manager import ModuleManager
from pts.action_manager import ActionManager
from pts.scrobbler import Scrobbler
from pts.session_manager import SessionManager
from sync.sync_manager import SyncManager

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata
from trakt import Trakt
import hashlib


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
        self.init()

        ModuleManager.initialize()

        Metadata.configure(
            cache=CacheManager.get('metadata'),
            client=Plex.client
        )

    def init(self):
        names = []

        # Initialize modules
        for module in self.modules:
            names.append(get_class_name(module))

            if hasattr(module, 'initialize'):
                module.initialize()

        log.info('Initialized %s modules: %s', len(names), ', '.join(names))

    @staticmethod
    def init_trakt():
        def get_credentials():
            password_hash = hashlib.sha1(Prefs['password'])

            return (
                Prefs['username'],
                password_hash.hexdigest()
            )

        Trakt.configure(
            # Application
            api_key='ba5aa61249c02dc5406232da20f6e768f3c82b28',

            # Version
            plugin_version=PLUGIN_VERSION,
            media_center_version=Plex.version(),

            # Account
            credentials=get_credentials
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
    def validate_auth(cls, retry_interval=30):
        if not Prefs['username'] or not Prefs['password']:
            log.warn('Authentication failed, username or password field empty')

            cls.update_config(False)
            return False

        success = Trakt['account'].test()

        if not success:
            # status - False = invalid credentials, None = request failed
            if success is False:
                log.warn('Authentication failed, username or password is incorrect')
            else:
                # Increase retry interval each time to a maximum of 30 minutes
                if retry_interval < 60 * 30:
                    retry_interval = int(retry_interval * 1.3)

                # Ensure we never go over 30 minutes
                if retry_interval > 60 * 30:
                    retry_interval = 60 * 30

                log.warn('Unable to verify account details, will try again in %s seconds', retry_interval)
                schedule(cls.validate_auth, retry_interval, retry_interval)

            Main.update_config(False)
            return False

        log.info('Authentication successful')

        Main.update_config(True)
        return True

    def start(self):
        # Validate username/password
        spawn(self.validate_auth)

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

    if Main.validate_auth():
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

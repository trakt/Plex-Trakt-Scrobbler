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
from core.logging_handler import PlexHandler
from core.logging_reporter import RAVEN
from core.helpers import spawn, get_pref, schedule, get_class_name, md5
from core.plugin import ART, NAME, ICON
from core.update_checker import UpdateChecker
from interface.main_menu import MainMenu
from plugin.core.constants import ACTIVITY_MODE, PLUGIN_VERSION, PLUGIN_IDENTIFIER
from plugin.modules.manager import ModuleManager
from pts.action_manager import ActionManager
from pts.scrobbler import Scrobbler
from pts.session_manager import SessionManager
from sync.sync_manager import SyncManager

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata, Matcher
from requests.packages.urllib3.util import Retry
from trakt import Trakt, ClientError
import logging
import os
import time


log = Logger()


class Main(object):
    modules = [
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

        # Initialize logging
        self.init_logging()

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
    def init_logging():
        level = PlexHandler.get_min_level('plugin')

        Log.Info('Changed %r logger level to %s', PLUGIN_IDENTIFIER, logging.getLevelName(level))

        # Update main logger level
        logger = logging.getLogger(PLUGIN_IDENTIFIER)
        logger.setLevel(level)

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

    @classmethod
    def init_trakt(cls):
        # Client
        Trakt.configuration.defaults.client(
            id='c9ccd3684988a7862a8542ae0000535e0fbd2d1c0ca35583af7ea4e784650a61',
            secret='bf00575b1ad252b514f14b2c6171fe650d474091daad5eb6fa890ef24d581f65'
        )

        # Application
        Trakt.configuration.defaults.app(
            name='trakt (for Plex)',
            version=PLUGIN_VERSION
        )

        # Setup request retrying
        Trakt.http.adapter_kwargs = {'max_retries': Retry(total=3, read=0)}
        Trakt.http.rebuild()

        Trakt.on('oauth.token_refreshed', cls.on_token_refreshed)

    @classmethod
    def on_token_refreshed(cls, authorization):
        log.debug('Authentication - PIN authorization refreshed')

        # Update stored authorization
        Dict['trakt.pin.authorization'] = authorization

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

    @classmethod
    def authenticate(cls, retry_interval=30):
        # Authenticate - PIN
        if cls.authenticate_pin():
            # Update trakt.py
            Trakt.configuration.defaults.oauth.from_response(
                Dict['trakt.pin.authorization']
            )

            # Update configuration
            Main.update_config(True)
            return True

        # Authenticate - AUTH (username/password)
        if cls.authenticate_auth():
            # Update trakt.py
            Trakt.configuration.defaults.auth(
                Dict['trakt.username'],
                Dict['trakt.token']
            )

            # Update configuration
            Main.update_config(True)
            return True

        # Authentication failure
        log.warn('Authentication failed')

        Main.update_config(False)
        return False

    @classmethod
    def authenticate_auth(cls):
        if not Dict['trakt.username'] or not Dict['trakt.token']:
            log.debug('Authentication - Unable to use AUTH (missing "trakt.username" or "trakt.token" properties)')
            return False

        log.info('Authentication - Using AUTH (username/password)')
        return True

    @classmethod
    def authenticate_pin(cls):
        if not Prefs['pin']:
            log.debug('Authentication - Unable to use PIN ("pin" field is empty)')
            return False

        if Dict['trakt.pin.authorization'] and Prefs['pin'] != Dict['trakt.pin.code']:
            # PIN changed, clear stored authorization
            Dict['trakt.pin.authorization'] = None
            Dict['trakt.pin.code'] = None

        if not Dict['trakt.pin.authorization']:
            # Exchange PIN for an authentication token
            authorization = Trakt['oauth'].token_exchange(
                code=Prefs['pin'],
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )

            if authorization:
                # Update stored authorization
                Dict['trakt.pin.authorization'] = authorization
                Dict['trakt.pin.code'] = Prefs['pin']
            else:
                # Clear stored authorization
                Dict['trakt.pin.authorization'] = None
                Dict['trakt.pin.code'] = None

        # Check if the exchange was successful
        if not Dict['trakt.pin.authorization']:
            log.debug('Authentication - Unable to use PIN (unable to exchange pin for an authentication token)')
            return False

        log.info('Authentication - Using PIN')
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

        # Start plex.activity.py
        Activity.start(ACTIVITY_MODE.get(Prefs['activity_mode']))


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

        def restart():
            # Delay until after `ValidatePrefs` returns
            time.sleep(3)

            # Restart plugin
            Plex[':/plugins'].restart(PLUGIN_IDENTIFIER)

        spawn(restart)
        return message

    # Re-initialize modules
    Main.init_logging()

    return message

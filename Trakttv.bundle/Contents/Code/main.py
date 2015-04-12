from core.cache import CacheManager
from core.configuration import Configuration
from core.header import Header
from core.helpers import get_class_name, md5
from core.logger import Logger
from core.logging_handler import PlexHandler
from core.logging_reporter import RAVEN
from core.update_checker import UpdateChecker
from sync.sync_manager import SyncManager

from plugin.core.constants import ACTIVITY_MODE, PLUGIN_VERSION, PLUGIN_IDENTIFIER
from plugin.core.helpers.thread import module_start
from plugin.modules.core.manager import ModuleManager

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata, Matcher
from requests.packages.urllib3.util import Retry
from trakt import Trakt
import logging
import os

log = Logger()


class Main(object):
    modules = [
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

        # TODO update account with new authorization

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

        # Start plex.activity.py
        Activity.start(ACTIVITY_MODE.get(Prefs['activity_mode']))

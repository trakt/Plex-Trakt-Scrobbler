from core.cache import CacheManager
from core.header import Header
from core.helpers import get_class_name, md5
from core.logger import Logger
from core.update_checker import UpdateChecker

from plugin.core.constants import ACTIVITY_MODE, PLUGIN_VERSION
from plugin.core.helpers.thread import module_start
from plugin.core.logger import LOG_HANDLER, update_loggers
from plugin.core.logger.handlers.error_reporter import RAVEN
from plugin.managers import TraktAccountManager
from plugin.models import TraktAccount
from plugin.modules.core.manager import ModuleManager
from plugin.preferences import Preferences

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata
from requests.packages.urllib3.util import Retry
from threading import Thread
from trakt import Trakt
import os
import uuid

log = Logger()


class Main(object):
    modules = [
        # core
        UpdateChecker()
    ]

    def __init__(self):
        Header.show(self)

        self.init_trakt()
        self.init_plex()
        self.init()

        ModuleManager.initialize()

        # Initialize sentry error reporting
        self.init_raven()

        # Construct main thread
        self.thread = Thread(target=self.run, name='main')

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
        # Ensure client identifier has been generated
        if not Dict['plex.client.identifier']:
            # Generate identifier
            Dict['plex.client.identifier'] = uuid.uuid4()

        # plex.py
        Plex.configuration.defaults.authentication(
            os.environ.get('PLEXTOKEN')
        )

        Plex.configuration.defaults.client(
            identifier=Dict['plex.client.identifier'],

            product='trakt (for Plex)',
            version=PLUGIN_VERSION
        )

        # plex.activity.py
        path = os.path.join(LOG_HANDLER.baseFilename, '..', '..', 'Plex Media Server.log')
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

        # Retrieve trakt account matching this `authorization`
        with Trakt.configuration.http(retry=True).oauth(token=authorization.get('access_token')):
            settings = Trakt['users/settings'].get()

        if not settings:
            log.warn('Authentication - Unable to retrieve account details for authorization')
            return

        # Retrieve trakt account username from `settings`
        username = settings.get('user', {}).get('username')

        if not username:
            log.warn('Authentication - Unable to retrieve username for authorization')
            return None

        # Find matching trakt account
        trakt_account = (TraktAccount
            .select()
            .where(
                TraktAccount.username == username
            )
        ).first()

        if not trakt_account:
            log.warn('Authentication - Unable to find TraktAccount with the username %r', username)

        # Update oauth credential
        TraktAccountManager.update.from_dict(trakt_account, {
            'authorization': {
                'oauth': authorization
            }
        })

        log.info('Authentication - Updated OAuth credential for %r', trakt_account)

    def start(self):
        self.thread.start()

    def run(self):
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
        Activity.start(ACTIVITY_MODE.get(Preferences.get('activity.mode')))

    @staticmethod
    def on_configuration_changed():
        update_loggers()

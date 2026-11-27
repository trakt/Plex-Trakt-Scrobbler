from core.header import Header
from core.helpers import get_class_name, spawn
from core.logger import Logger

from plugin.core.configuration import Configuration
from plugin.core.constants import ACTIVITY_MODE, PLUGIN_VERSION
from plugin.core.helpers.thread import module_start
from plugin.core.logger import LOG_HANDLER, LoggerManager
from plugin.managers.account import TraktAccountManager
from plugin.managers.m_trakt.authentication import TraktAuthenticationManager
from plugin.models import TraktAccount
from plugin.modules.core.manager import ModuleManager
from plugin.preferences import Preferences
from plugin.scrobbler.core.session_prefix import SessionPrefix

from plex import Plex
from plex_activity import Activity
from plex_metadata import Metadata
from six.moves.urllib.parse import quote_plus, urlsplit, urlunsplit
from requests.packages.urllib3.util import Retry
from trakt import Trakt
import os
import uuid

log = Logger()


class Main(object):
    modules = []

    def __init__(self):
        Header.show(self)

        # Initial configuration update
        self.on_configuration_changed()

        # Initialize clients
        self.init_trakt()
        self.init_plex()
        self.init()

        # Initialize modules
        ModuleManager.initialize()

    def init(self):
        names = []

        # Initialize modules
        for module in self.modules:
            names.append(get_class_name(module))

            if hasattr(module, 'initialize'):
                module.initialize()

        log.info('Initialized %s modules: %s', len(names), ', '.join(names))

    @staticmethod
    def init_plex():
        # Ensure client identifier has been generated
        if not Dict['plex.client.identifier']:
            # Generate identifier
            Dict['plex.client.identifier'] = uuid.uuid4()

        # Retrieve current client identifier
        client_id = Dict['plex.client.identifier']

        if isinstance(client_id, uuid.UUID):
            client_id = str(client_id)

        # plex.py
        Plex.configuration.defaults.authentication(
            os.environ.get('PLEXTOKEN')
        )

        Plex.configuration.defaults.client(
            identifier=client_id,

            product='trakt (for Plex)',
            version=PLUGIN_VERSION
        )

        # plex.activity.py
        path = os.path.join(LOG_HANDLER.baseFilename, '..', '..', 'Plex Media Server.log')
        path = os.path.abspath(path)

        Activity['logging'].add_hint(path)

        # plex.metadata.py
        Metadata.configure(
            client=Plex.client
        )

    @classmethod
    def init_trakt(cls):
        config = Configuration.advanced['trakt']

        # Build timeout value
        timeout = (
            config.get_float('connect_timeout', 6.05),
            config.get_float('read_timeout', 24)
        )

        # Client: no Client Secret. Client ID is required; not embedded.
        # advanced.ini:
        #   [trakt]
        #   client_id = YOUR_CLIENT_ID
        client_id = (
            config.get('client_id') or
            config.get('client.id') or
            os.environ.get('TRAKT_CLIENT_ID') or
            ''
        )

        Trakt.configuration.defaults.client(
            id=client_id,
            secret=None
        )

        # Application
        Trakt.configuration.defaults.app(
            name='trakt (for Plex)',
            version=PLUGIN_VERSION
        )

        # Http
        Trakt.base_url = (
            config.get('protocol', 'https') + '://' +
            config.get('hostname', 'api.trakt.tv')
        )

        Trakt.configuration.defaults.http(
            timeout=timeout
        )

        # Configure keep-alive
        Trakt.http.keep_alive = config.get_boolean('keep_alive', True)

        # Configure requests adapter
        Trakt.http.adapter_kwargs = {
            'pool_connections': config.get_int('pool_connections', 10),
            'pool_maxsize': config.get_int('pool_size', 10),
            'max_retries': Retry(
                total=config.get_int('connect_retries', 3),
                read=0
            )
        }

        Trakt.http.rebuild()

        # Authentication manager is authoritative for refresh + persistence.
        TraktAuthenticationManager.configure(
            client_id=client_id,
            timeout=timeout,
            session=Trakt.http.session,
        )

        # Bind to events. Event concept retained; no second refresh implementation.
        Trakt.on('oauth.refresh', cls.on_trakt_refresh)
        Trakt.on('oauth.refresh.rejected', cls.on_trakt_refresh_rejected)

        log.info(
            'Configured trakt.py (timeout=%r, base_url=%r, keep_alive=%r, adapter_kwargs=%r)',
            timeout,
            Trakt.base_url,
            Trakt.http.keep_alive,
            Trakt.http.adapter_kwargs,
        )

    @classmethod
    def on_trakt_refresh(cls, username, authorization):
        # `TraktAuthenticationManager` is authoritative for persistence.
        # Retain event integration; do not persist a second time.
        log.info('[Trakt.tv] Access token refreshed for %r', username)
        return True

    @classmethod
    def on_trakt_refresh_rejected(cls, username, reason=None):
        log.info('[Trakt.tv] Refresh rejected: %s', reason or 'invalid_grant')

        # Find matching trakt account. Do not delete account or clear associations.
        account = (TraktAccount
            .select()
            .where(
                TraktAccount.username == username
            )
        ).first()

        if not account:
            log.warn('[Trakt.tv] Unable to find account with the username: %r', username)
            return False

        # Mark credentials invalid / require reauthorization; preserve record.
        account.auth_state = 'authorization_required'
        account.save()

        log.info('[Trakt.tv] Account requires reauthorization: %r', account)
        return True

    def start(self):
        # Construct main thread
        spawn(self.run, daemon=True, thread_name='main')

    def run(self):
        # Check for authentication token
        log.info('X-Plex-Token: %s', 'available' if os.environ.get('PLEXTOKEN') else 'unavailable')

        # Process server startup state
        self.process_server_state()

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

    @classmethod
    def process_server_state(cls):
        # Check startup state
        server = Plex.detail()

        if server is None:
            log.info('Unable to check startup state, detail request failed')
            return

        # Check server startup state
        if server.start_state is None:
            return

        if server.start_state == 'startingPlugins':
            return cls.on_starting_plugins()

        log.error('Unhandled server start state %r', server.start_state)

    @staticmethod
    def on_starting_plugins():
        log.debug('on_starting_plugins')

        SessionPrefix.increment()

    @classmethod
    def on_configuration_changed(cls):
        # Update proxies (for requests)
        cls.update_proxies()

        # Refresh loggers
        LoggerManager.refresh()

    @staticmethod
    def update_proxies():
        # Retrieve proxy host
        host = Prefs['proxy_host']

        if not host:
            if not Trakt.http.proxies and not os.environ.get('HTTP_PROXY') and not os.environ.get('HTTPS_PROXY'):
                return

            # Update trakt client
            Trakt.http.proxies = {}

            # Update environment variables
            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']

            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']

            log.info('HTTP Proxy has been disabled')
            return

        # Parse URL
        host_parsed = urlsplit(host)

        # Expand components
        scheme, netloc, path, query, fragment = host_parsed

        if not scheme:
            scheme = 'http'

        # Retrieve proxy credentials
        username = Prefs['proxy_username']
        password = Prefs['proxy_password']

        # Build URL
        if username and password and '@' not in netloc:
            netloc = '%s:%s@%s' % (
                quote_plus(username),
                quote_plus(password),
                netloc
            )

        url = urlunsplit((scheme, netloc, path, query, fragment))

        # Update trakt client
        Trakt.http.proxies = {
            'http': url,
            'https': url
        }

        # Update environment variables
        os.environ.update({
            'HTTP_PROXY': url,
            'HTTPS_PROXY': url
        })

        # Display message in log file
        if not host_parsed.username and not host_parsed.password:
            log.info('HTTP Proxy has been enabled (host: %r)', host)
        else:
            log.info('HTTP Proxy has been enabled (host: <sensitive>)')

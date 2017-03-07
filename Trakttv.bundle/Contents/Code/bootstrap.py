from plugin.core.constants import PLUGIN_VERSION, PLUGIN_NAME
from plugin.core.helpers.thread import spawn

from datetime import datetime
import inspect

# http://bugs.python.org/issue7980
datetime.strptime('', '')


def task(*args, **kwargs):
    def wrapper(func):
        func.optional = kwargs.get('optional', False)

        func.priority = args
        func.task = True

        return func

    return wrapper


class Bootstrap(object):
    class Groups(object):
        Initialize  = 1000
        Configure   = 2000
        Start       = 3000

    debug = False

    def __init__(self):
        self.finished = False

    def discover(self):
        tasks = []

        for name in dir(self):
            if name.startswith('_'):
                continue

            value = getattr(self, name)

            if not inspect.ismethod(value):
                continue

            if not hasattr(value, 'task') or not hasattr(value, 'priority'):
                continue

            tasks.append(value)

        return sorted(tasks, key=lambda t: t.priority)

    def start(self):
        spawn(self.run, daemon=True, thread_name='bootstrap')

    def run(self):
        tasks = self.discover()

        if self.debug:
            Log.Debug('Starting %d task(s)...' % (len(tasks),))

        for func in tasks:
            name = func.__name__

            if self.debug:
                Log.Debug('Task \'%s\' started' % (name,))

            try:
                func()

                if self.debug:
                    Log.Debug('Task \'%s\' finished' % (name,))
            except Exception as ex:
                if not func.optional:
                    Log.Error('Unable to bootstrap plugin, task \'%s\' raised: %s' % (name, ex))
                    return False

                Log.Warn('Task \'%s\' raised: %s' % (name, ex))

        if self.debug:
            Log.Debug('Finished %d task(s)' % (len(tasks),))

        self.finished = True

    #
    # Header
    #

    @task()
    def header(self):
        def line(contents):
            Log.Info('| ' + str(contents))

        def separator(ch):
            Log.Info(ch * 50)

        separator('=')
        line(PLUGIN_NAME)
        line('https://github.com/trakt/Plex-Trakt-Scrobbler')
        separator('-')
        line('Current Version: %s' % (PLUGIN_VERSION,))
        separator('=')

    #
    # Initialize
    #

    @task(Groups.Initialize, 10)
    def initialize_environment(self):
        from plugin.core.environment import Environment
        import os

        Environment.setup(Core, Dict, Platform, Prefs)

        # plex.database.py
        os.environ['LIBRARY_DB'] = os.path.join(
            Environment.path.plugin_support, 'Databases',
            'com.plexapp.plugins.library.db'
        )

    @task(Groups.Initialize, 20)
    def initialize_filesystem(self):
        from fs_migrator import FSMigrator

        FSMigrator.run()

    @task(Groups.Initialize, 30)
    def initialize_logging(self):
        from plugin.core.logger import LoggerManager

        LoggerManager.setup(storage=False)
        LoggerManager.refresh()

    @task(Groups.Initialize, 40)
    def initialize_interface_messages(self):
        from plugin.core.message import InterfaceMessages

        InterfaceMessages.bind()

    @task(Groups.Initialize, 50)
    def initialize_locale(self):
        from plugin.core.environment import Environment

        Environment.setup_locale()
        Environment.setup_translation()

    @task(Groups.Initialize, 60)
    def initialize_native_libraries(self):
        from plugin.core.libraries.manager import LibrariesManager

        LibrariesManager.setup(cache=True)
        LibrariesManager.test()

    @task(Groups.Initialize, 70)
    def initialize_warnings(self):
        from requests.packages.urllib3.exceptions import InsecurePlatformWarning, SNIMissingWarning
        import warnings

        warnings.filterwarnings('once', category=InsecurePlatformWarning)
        warnings.filterwarnings('once', category=SNIMissingWarning)

    @task(Groups.Initialize, 90)
    def initialize_singleton(self):
        from plugin.core.singleton import Singleton

        if not Singleton.acquire():
            Log.Warn('Unable to acquire plugin instance')

    @task(Groups.Initialize, 100)
    def initialize_logging_storage(self):
        from plugin.core.logger import LoggerManager

        LoggerManager.setup(storage=True)

    #
    # Configure
    #

    @task(Groups.Configure, 10)
    def configure_proxies(self):
        # Update proxies (for requests)
        self.update_proxies()

    @task(Groups.Configure, 20)
    def configure_loggers(self):
        from plugin.core.logger import LoggerManager

        # Refresh logger levels
        LoggerManager.refresh()

    @task(Groups.Configure, 30)
    def configure_trakt(self):
        from plugin.core.configuration import Configuration

        from requests.packages.urllib3.util import Retry
        from trakt import Trakt

        config = Configuration.advanced['trakt']

        # Build timeout value
        timeout = (
            config.get_float('connect_timeout', 6.05),
            config.get_float('read_timeout', 24)
        )

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

        # Bind to events
        Trakt.on('oauth.refresh', self.on_trakt_refresh)
        Trakt.on('oauth.refresh.rejected', self.on_trakt_refresh_rejected)

        Log.Info('Configured trakt.py (timeout=%r, base_url=%r, keep_alive=%r, adapter_kwargs=%r)' % (
            timeout,
            Trakt.base_url,
            Trakt.http.keep_alive,
            Trakt.http.adapter_kwargs,
        ))

    @task(Groups.Configure, 40)
    def configure_plex(self):
        from plugin.core.logger import LOG_HANDLER

        from plex import Plex
        from plex_activity import Activity
        from plex_metadata import Metadata
        import os
        import uuid

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

    #
    # Start
    #

    @task(Groups.Start, 0)
    def start_module_initialization(self):
        from plugin.modules.core.manager import ModuleManager

        # Initialize modules
        ModuleManager.initialize()

    @task(Groups.Start, 10)
    def start_token_exists(self):
        import os

        Log.Info('X-Plex-Token: %s', 'available' if os.environ.get('PLEXTOKEN') else 'unavailable')

    @task(Groups.Start, 20)
    def start_check_server_state(self):
        from plex import Plex

        # Check startup state
        server = Plex.detail()

        if server is None:
            Log.Info('Unable to check startup state, detail request failed')
            return

        # Check server startup state
        if server.start_state is None:
            return

        if server.start_state == 'startingPlugins':
            return self.on_starting_plugins()

        Log.Warn('Unhandled server start state %r' % (server.start_state,))

    @task(Groups.Start, 100)
    def start_modules(self):
        from plugin.core.helpers.thread import module_start
        from plugin.modules.core.manager import ModuleManager

        # Start old-style modules
        module_start()

        # Start new-style modules
        ModuleManager.start()

    @task(Groups.Start, 200)
    def start_plex_activity(self):
        from plugin.core.constants import ACTIVITY_MODE
        from plugin.preferences import Preferences

        from plex_activity import Activity

        # Start plex.activity.py
        Activity.start(ACTIVITY_MODE.get(Preferences.get('activity.mode')))

    @task(Groups.Start, 210)
    def start_update_checker(self):
        from core.update_checker import UpdateChecker

        checker = UpdateChecker()
        checker.start()

    #
    # Event handlers
    #

    @classmethod
    def on_configuration_changed(cls):
        from plugin.core.logger import LoggerManager

        # Update proxies (for requests)
        cls.update_proxies()

        # Refresh logger levels
        LoggerManager.refresh()

    @staticmethod
    def on_starting_plugins():
        from plugin.scrobbler.core.session_prefix import SessionPrefix

        Log.Debug('Server is starting up, incrementing session prefix...')

        SessionPrefix.increment()

    @staticmethod
    def on_trakt_refresh(username, authorization):
        from plugin.managers.account import TraktAccountManager
        from plugin.models import TraktAccount

        from trakt import Trakt

        Log.Debug('[Trakt.tv] Token has been refreshed for %r' % (username,))

        # Retrieve trakt account matching this `authorization`
        with Trakt.configuration.http(retry=True).oauth(token=authorization.get('access_token')):
            settings = Trakt['users/settings'].get(validate_token=False)

        if not settings:
            Log.Warn('[Trakt.tv] Unable to retrieve account details for token')
            return False

        # Retrieve trakt account username from `settings`
        s_username = settings.get('user', {}).get('username')

        if not s_username:
            Log.Warn('[Trakt.tv] Unable to retrieve username for token')
            return False

        if s_username != username:
            Log.Warn('[Trakt.tv] Token mismatch (%r != %r)', s_username, username)
            return False

        # Find matching trakt account
        trakt_account = (TraktAccount
            .select()
            .where(
                TraktAccount.username == username
            )
        ).first()

        if not trakt_account:
            Log.Warn('[Trakt.tv] Unable to find account with the username: %r', username)
            return False

        # Update OAuth credential
        TraktAccountManager.update.from_dict(
            trakt_account, {
                'authorization': {
                    'oauth': authorization
                }
            },
            settings=settings
        )

        Log.Info('[Trakt.tv] Token updated for %r', trakt_account)
        return True

    @staticmethod
    def on_trakt_refresh_rejected(username):
        from plugin.managers.m_trakt.credential import TraktOAuthCredentialManager
        from plugin.models import TraktAccount

        Log.Debug('[Trakt.tv] Token refresh for %r has been rejected', username)

        # Find matching trakt account
        account = (TraktAccount
            .select()
            .where(
                TraktAccount.username == username
            )
        ).first()

        if not account:
            Log.Warn('[Trakt.tv] Unable to find account with the username: %r', username)
            return False

        # Delete OAuth credential
        TraktOAuthCredentialManager.delete(
            account=account.id
        )

        Log.Info('[Trakt.tv] Token cleared for %r', account)
        return True

    #
    # Actions
    #

    @staticmethod
    def update_proxies():
        from six.moves.urllib.parse import quote_plus, urlsplit, urlunsplit
        from trakt import Trakt
        import os

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

            Log.Info('HTTP Proxy has been disabled')
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
            Log.Info('HTTP Proxy has been enabled (host: %r)' % (host,))
        else:
            Log.Info('HTTP Proxy has been enabled (host: <sensitive>)')



bootstrap = Bootstrap()

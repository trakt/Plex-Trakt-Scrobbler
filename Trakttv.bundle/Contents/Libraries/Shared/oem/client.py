from oem.services import SERVICES
from oem.providers import PROVIDERS
from oem.providers.core.base import Provider
from oem.version import __version__
from oem_core.core.plugin import PluginManager

import logging
import six

log = logging.getLogger(__name__)

DATABASES = {
    ('anidb', 'tvdb'): 'oem_database_anidb_tvdb',
    ('tvdb', 'anidb'): 'oem_database_anidb_tvdb',

    ('anidb', 'imdb'): 'oem_database_anidb_imdb',
    ('imdb', 'anidb'): 'oem_database_anidb_imdb'
}

PACKAGES = {
    ('anidb', 'tvdb'): 'oem-database-anidb-tvdb',
    ('tvdb', 'anidb'): 'oem-database-anidb-tvdb',

    ('anidb', 'imdb'): 'oem-database-anidb-imdb',
    ('imdb', 'anidb'): 'oem-database-anidb-imdb'
}


class Client(object):
    version = __version__

    def __init__(self, formats=None, provider='package'):
        """OpenEntityMap (OEM) Client

        :param formats: List of formats to use, or `None` for any
        :type formats: list or None

        :param provider: Source to use for databases
        :type provider: str or oem.sources.core.base.Source
        """

        self._formats = formats

        # Discover available plugins
        self._plugins = PluginManager
        self._plugins.discover()

        # Construct plugins
        self._provider = self._construct_provider(provider)
        self._services = self._construct_services()  # { (<source>, <target>): <service> }

    @property
    def formats(self):
        return self._formats

    @property
    def plugins(self):
        return self._plugins

    @property
    def provider(self):
        return self._provider

    def load_all(self):
        for service in six.itervalues(self._services):
            service.load()

    def database_name(self, source, target):
        return DATABASES.get((source, target))

    def package_name(self, source, target):
        return PACKAGES.get((source, target))

    def __getitem__(self, source):
        return ServiceInterface(self, source)

    #
    # Private methods
    #

    def _construct_services(self):
        result = {}

        for key, cls in SERVICES.items():
            # Add supported service conversions
            for source, targets in cls.__services__.items():
                for target in targets:
                    # Construct service
                    result[(source, target)] = cls(self, source, target)

        return result

    def _construct_provider(self, provider_or_key):
        if isinstance(provider_or_key, Provider):
            # Use provided source
            provider = provider_or_key
        elif provider_or_key in PROVIDERS:
            # Construct source by key
            provider = PROVIDERS[provider_or_key]()
        else:
            raise ValueError('Unknown provider: %r' % provider_or_key)

        # Initialize source
        provider.initialize(self)
        return provider


class ServiceInterface(object):
    def __init__(self, client, source):
        self.client = client
        self.source = source

    def to(self, target):
        try:
            return self.client._services[(self.source, target)]
        except KeyError:
            raise KeyError('Unknown service: %s -> %s' % (self.source, target))

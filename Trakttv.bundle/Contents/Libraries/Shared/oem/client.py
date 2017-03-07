from __future__ import absolute_import, division, print_function

from oem.core.providers.base import Provider
from oem.version import __version__
from oem_core.core.plugin import PluginManager

import inspect
import logging
import six

log = logging.getLogger(__name__)


class Client(object):
    version = __version__

    def __init__(self, services, provider, formats=None):
        """Client for OpenEntityMap.

        :param services: List of services to load (e.g. "anidb")
        :type services: list

        :param provider: Provider to use for databases (e.g. "package", "release/incremental")
        :type provider: str or oem.core.providers.base.Base

        :param formats: List of formats to use, or `None` for any
        :type formats: list or None
        """

        self._formats = formats

        # Discover available plugins
        self._plugins = PluginManager
        self._plugins.discover()

        # Construct plugins
        self._services = self._construct_services(services)
        self._provider = self._construct_provider(provider)

        # Build database + package tables
        self._databases = {}
        self._packages = {}

        for _, cls in self._load_plugins('client', services, construct=False):
            # Merge service databases into client
            if cls.__databases__:
                self._databases.update(cls.__databases__)
            else:
                log.warn('Service %r has no "__databases__" defined', cls.__key__)

            # Merge service packages into client
            if cls.__packages__:
                self._packages.update(cls.__packages__)
            else:
                log.warn('Service %r has no "__packages__" defined', cls.__key__)

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
        return self._databases.get((source, target))

    def package_name(self, source, target):
        return self._packages.get((source, target))

    def __getitem__(self, source):
        return ServiceInterface(self, source)

    #
    # Private methods
    #

    def _construct_services(self, services):
        result = {}

        for _, cls in self._load_plugins('client', services, construct=False):
            # Add supported service conversions
            for source, targets in cls.__services__.items():
                for target in targets:
                    # Construct service
                    result[(source, target)] = cls(self, source, target)

        return result

    def _construct_provider(self, provider_or_key):
        if isinstance(provider_or_key, Provider):
            # Class
            provider = provider_or_key
        elif isinstance(provider_or_key, six.string_types):
            # Identifier
            provider = PluginManager.get('client-provider', provider_or_key)

            if provider is None:
                raise ValueError('Unable to find provider: %r' % provider_or_key)
        else:
            raise ValueError('Unknown provider: %r' % provider_or_key)

        # Ensure provider has been constructed
        if inspect.isclass(provider):
            provider = provider()

        # Initialize provider
        provider.initialize(self)
        return provider

    @staticmethod
    def _load_plugins(kind, keys, construct=True):
        if not keys:
            return

        for name in keys:
            cls = PluginManager.get(kind, name)

            if cls is None:
                log.warn('Unable to find plugin: %r', name)
                continue

            if not cls.available:
                log.warn('Plugin %r is not available', name)
                continue

            if construct:
                yield cls.__key__, cls()
            else:
                yield cls.__key__, cls


class ServiceInterface(object):
    def __init__(self, client, source):
        self.client = client
        self.source = source

    def to(self, target):
        try:
            return self.client._services[(self.source, target)]
        except KeyError:
            raise KeyError('Unknown service: %s -> %s' % (self.source, target))

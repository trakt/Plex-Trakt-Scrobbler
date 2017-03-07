from __future__ import absolute_import, division, print_function

from oem_core.core.plugin import PluginManager
from oem_framework.plugin import Plugin
from oem_framework.storage import ProviderStorage


class Provider(Plugin):
    def __init__(self, storage):
        self._storage = storage

        self._client = None

    #
    # Properties
    #

    @property
    def client(self):
        return self._client

    @property
    def formats(self):
        return self._client.formats

    @property
    def plugins(self):
        return self._client.plugins

    @property
    def storage(self):
        return self._storage

    #
    # Public methods
    #

    def initialize(self, client):
        self._client = client

        self._storage = self._construct_storage(self._storage)

    #
    # Abstract methods
    #

    def fetch(self, source, target, key, metadata):
        raise NotImplementedError

    def open_database(self, source, target):
        raise NotImplementedError

    #
    # Private methods
    #

    def _construct_storage(self, storage_or_key):
        if isinstance(storage_or_key, ProviderStorage):
            # Use provided source
            storage = storage_or_key
        elif PluginManager.has('storage', storage_or_key):
            # Construct source by key
            storage = PluginManager.get('storage', storage_or_key)()
        else:
            raise ValueError('Unknown storage interface: %r' % storage_or_key)

        # Initialize source
        storage.initialize(self._client)
        return storage

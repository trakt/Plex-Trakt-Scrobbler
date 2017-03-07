from __future__ import absolute_import, division, print_function

from oem_framework.core.elapsed import Elapsed
from oem_framework.plugin import Plugin

import logging

log = logging.getLogger(__name__)


class Service(Plugin):
    __databases__ = {}
    __packages__ = {}
    __services__ = {}

    def __init__(self, client, source, target, formats=None):
        self._client = client
        self._source = source
        self._target = target
        self._formats = formats

        self._database = None
        self._collection = None
        self._loaded = False

    @property
    def database_name(self):
        return 'oem_database_%s_%s' % (self._source, self._target)

    @property
    def loaded(self):
        return self._loaded

    @property
    def package_name(self):
        return 'oem-database-%s-%s' % (self._source, self._target)

    @property
    def provider(self):
        return self._client._provider

    @property
    def source_key(self):
        return self._source

    @property
    def target_key(self):
        return self._target

    @Elapsed.track
    def load(self):
        if self._loaded:
            return True

        # Load database
        self._database = self.provider.open_database(
            self.source_key,
            self.target_key
        )

        if self._database is None:
            log.warn('Unable to load database for: %s -> %s', self.source_key, self.target_key)
            return False

        # Load collection
        self._collection = self._database.load_collection(
            self._source,
            self._target
        )

        if self._collection is None:
            log.warn('Unable to load collection for: %s -> %s', self.source_key, self.target_key)
            return False

        # Successfully loaded service
        log.info('Loaded service: %-5s -> %-5s (storage: %r)', self._source, self._target, self._database.storage)
        self._loaded = True

        return True

    @Elapsed.track
    def fetch(self, key, metadata):
        # Ensure database is loaded
        if not self.load():
            return False

        # Ensure item is loaded
        return self.provider.fetch(
            self.source_key,
            self.target_key,
            key, metadata
        )

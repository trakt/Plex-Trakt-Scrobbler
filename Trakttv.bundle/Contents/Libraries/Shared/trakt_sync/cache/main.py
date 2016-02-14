from trakt_sync.cache.sources import ListSource, SyncSource
from pyemitter import Emitter
import trakt_sync.cache.enums as enums

import logging

log = logging.getLogger(__name__)


class Cache(object):
    Data = enums.Data
    Media = enums.Media

    def __init__(self, media, data, storage):
        self.storage = storage

        self.collections = self.storage('collections')
        self.events = Emitter()
        self.stores = {}

        self.media = Cache.Media.parse(media)
        self.data = Cache.Data.parse(data)

        # Construct sources
        self._sources = {
            'list': ListSource(self),
            'sync': SyncSource(self)
        }

    def invalidate(self, key):
        # Retrieve collection from database
        collection = self._get_collection(*key)

        # Reset collection timestamps
        collection['timestamps'] = {}

    def refresh(self, username):
        for source in self._sources.values():
            for result in source.refresh(username):
                yield result

    def source(self, key):
        return self._sources.get(key)

    def _get_collection(self, username, *args):
        key = tuple([username] + list(args))

        if key not in self.collections:
            self.collections[key] = {}

        collection = self.collections[key]

        collection['store'] = self._get_store(*key)

        if 'timestamps' not in collection:
            collection['timestamps'] = {}

        return collection

    def _get_store(self, username, *args):
        key = tuple([username] + list(args))

        if key not in self.stores:
            self.stores[key] = self.storage('stores.%s' % ('.'.join(key)))

        return self.stores[key]

    def __getitem__(self, key):
        collection = self._get_collection(*key)

        return collection['store']

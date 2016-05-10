from oem_framework import models
from oem_framework.core.elapsed import Elapsed
from oem_framework.storage import DatabaseStorage

import logging

log = logging.getLogger(__name__)


class Database(models.Database):
    @classmethod
    def load(cls, storage, source, target):
        if not isinstance(storage, DatabaseStorage):
            raise ValueError('Invalid value provided for the "storage" parameter')

        # Construct database
        database = cls(storage, source, target)
        return database

    @Elapsed.track
    def load_collection(self, source, target):
        collection = self.collections[source] = self.storage.open_collection(source, target)
        return collection

    @Elapsed.track
    def load_collections(self, collections=None):
        if collections is None:
            raise NotImplementedError

        for source, target in collections:
            # Load collection
            self.load_collection(source, target)

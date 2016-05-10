from oem_framework import models
from oem_framework.core.elapsed import Elapsed
from oem_framework.storage import IndexStorage

import logging

log = logging.getLogger(__name__)


class Index(models.Index):
    @classmethod
    @Elapsed.track
    def load(cls, collection, storage):
        if not isinstance(storage, IndexStorage):
            raise ValueError('Invalid value provided for the "storage" parameter')

        # Construct collection
        return storage.load(collection)

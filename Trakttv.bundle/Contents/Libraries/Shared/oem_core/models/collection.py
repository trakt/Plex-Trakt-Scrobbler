from oem_framework import models
from oem_framework.core.elapsed import Elapsed
from oem_framework.storage import CollectionStorage

import logging

log = logging.getLogger(__name__)


class Collection(models.Collection):
    @classmethod
    @Elapsed.track
    def load(cls, storage, source=None, target=None):
        """Load collection from `storage`

        :param storage: Storage interface
        :type storage: CollectionStorage

        :param source: Name of source service
        :type source: str

        :param target: Name of target service
        :type target: str

        :rtype: Collection
        """

        if not isinstance(storage, CollectionStorage):
            raise ValueError('Invalid value provided for the "storage" parameter')

        # Construct collection
        collection = cls(storage, source, target)
        collection.index = storage.open_index(collection)
        return collection

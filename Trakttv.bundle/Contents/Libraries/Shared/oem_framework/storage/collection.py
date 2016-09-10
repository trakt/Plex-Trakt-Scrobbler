from oem_framework.storage.core.base import BaseStorage


class CollectionStorage(BaseStorage):
    @classmethod
    def open(cls, parent, source, target, version=None):
        """
        :rtype: CollectionStorage
        """
        raise NotImplementedError

    def open_index(self, collection):
        """
        :rtype: oem_framework.models.Index
        """
        raise NotImplementedError

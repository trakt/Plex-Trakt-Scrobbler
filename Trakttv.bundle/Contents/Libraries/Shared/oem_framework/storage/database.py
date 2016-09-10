from oem_framework.storage.core.base import BaseStorage


class DatabaseStorage(BaseStorage):
    @classmethod
    def open(cls, parent, source, target, version=None):
        """
        :rtype: DatabaseStorage
        """
        raise NotImplementedError

    def open_collection(self, source, target):
        """
        :rtype: oem_framework.models.Collection
        """
        raise NotImplementedError

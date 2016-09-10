from oem_framework.storage.core.base import BaseStorage


class IndexStorage(BaseStorage):
    @classmethod
    def open(cls, parent):
        """
        :rtype: IndexStorage
        """
        raise NotImplementedError

    def get(self, index, key):
        raise NotImplementedError

    def load(self, collection):
        """
        :rtype: oem_framework.models.Index
        """
        raise NotImplementedError

    def parse(self, collection, key, value):
        """
        :rtype: oem_framework.models.Metadata
        """
        raise NotImplementedError

from oem_framework.storage.core.base import BaseStorage


class MetadataStorage(BaseStorage):
    @classmethod
    def open(cls, parent, key):
        """
        :rtype: MetadataStorage
        """
        raise NotImplementedError

    def open_item(self, collection, media):
        """

        :rtype: oem_framework.models.Item
        """
        raise NotImplementedError

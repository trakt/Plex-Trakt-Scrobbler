from oem_framework.storage.core.base import BaseStorage


class ItemStorage(BaseStorage):
    @classmethod
    def open(cls, parent, key):
        """
        :rtype: ItemStorage
        """
        raise NotImplementedError

    def load(self, collection, media):
        """

        :rtype: oem_framework.models.Item
        """
        raise NotImplementedError

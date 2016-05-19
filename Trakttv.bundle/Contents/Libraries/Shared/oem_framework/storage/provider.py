from oem_framework.storage.core.base import BaseStorage


class ProviderStorage(BaseStorage):
    @classmethod
    def open(cls, client, path=None):
        """
        :rtype: ProviderStorage
        """
        raise NotImplementedError

    #
    # Provider methods
    #

    def create(self, source, target):
        """
        :rtype: bool
        """
        raise NotImplementedError

    def open_database(self, source, target):
        """
        :rtype: oem_framework.models.Database
        """
        raise NotImplementedError

    #
    # Collection methods
    #

    def has_collection(self, source, target):
        raise NotImplementedError

    def get_collection_version(self, source, target):
        raise NotImplementedError

    def update_collection(self, source, target, version):
        raise NotImplementedError

    #
    # Index methods
    #

    def update_index(self, source, target, response):
        """
        :rtype: bool
        """
        raise NotImplementedError

    #
    # Item methods
    #

    def has_item(self, source, target, key):
        """
        :rtype: bool
        """
        raise NotImplementedError

    def update_item(self, source, target, key, response, metadata):
        """
        :rtype: bool
        """
        raise NotImplementedError

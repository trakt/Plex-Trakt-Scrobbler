from oem_framework.plugin import Plugin
from oem_framework.storage import MetadataStorage
from oem_storage_codernitydb.item import ItemCodernityDbStorage


class MetadataCodernityDbStorage(MetadataStorage, Plugin):
    __key__ = 'codernitydb/metadata'

    def __init__(self, parent, key):
        super(MetadataCodernityDbStorage, self).__init__()

        self.parent = parent
        self.key = key

    @classmethod
    def open(cls, parent, key):
        storage = cls(parent, key)
        storage.initialize(parent._client)
        return storage

    def open_item(self, collection, media):
        storage = ItemCodernityDbStorage.open(self.parent, self.key)
        return storage.load(collection, media)

from oem_framework.models.core import ModelRegistry
from oem_framework.plugin import Plugin
from oem_framework.storage import CollectionStorage
from oem_storage_codernitydb.index import IndexCodernityDbStorage


class CollectionCodernityDbStorage(CollectionStorage, Plugin):
    __key__ = 'codernitydb/collection'

    def __init__(self, parent, source, target, version=None):
        super(CollectionCodernityDbStorage, self).__init__()

        self.parent = parent
        self.source = source
        self.target = target
        self.version = version

    @classmethod
    def open(cls, parent, source, target, version=None):
        storage = cls(parent, source, target, version)
        storage.initialize(parent._client)
        return storage

    def open_index(self, collection):
        return ModelRegistry['Index'].load(collection, IndexCodernityDbStorage.open(self))

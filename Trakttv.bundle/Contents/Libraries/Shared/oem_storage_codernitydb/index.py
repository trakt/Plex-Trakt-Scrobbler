from oem_framework.models.core import ModelRegistry
from oem_framework.plugin import Plugin
from oem_framework.storage import IndexStorage
from oem_storage_codernitydb.metadata import MetadataCodernityDbStorage

from CodernityDB.database import RecordNotFound


class IndexCodernityDbStorage(IndexStorage, Plugin):
    __key__ = 'codernitydb/index'

    def __init__(self, parent):
        super(IndexCodernityDbStorage, self).__init__()

        self.parent = parent

        self.name = None

    @classmethod
    def open(cls, parent):
        storage = cls(parent)
        storage.initialize(parent._client)
        return storage

    def get(self, index, key):
        try:
            item = self.main.database.get('metadata_key', (self.parent.source, self.parent.target, key), with_doc=True)
        except RecordNotFound:
            return None

        if not item or 'doc' not in item:
            return None

        return self.parse(index.collection, key, item['doc'])

    def load(self, collection):
        index = ModelRegistry['Index'](collection, self)
        index.items = None
        return index

    def parse(self, collection, key, value):
        attributes = value.get('_', {})

        if attributes.get('e'):
            # Decode metadata
            value = self.format.decode(
                ModelRegistry['Metadata'], value,
                ignore_keys=['_', '_id', '_rev']
            )

            # Remove "e" (encoded) attribute
            del value['_']['e']

            # Update item in database
            self.main.database.update(value)

        return ModelRegistry['Metadata'].from_dict(
            collection, value,
            key=str(key),
            storage=MetadataCodernityDbStorage.open(self.parent, key)
        )

from oem_framework.models.core import ModelRegistry
from oem_framework.plugin import Plugin
from oem_framework.storage import ItemStorage

from CodernityDB.database import RecordNotFound


class ItemCodernityDbStorage(ItemStorage, Plugin):
    __key__ = 'codernitydb/item'

    def __init__(self, parent, key):
        super(ItemCodernityDbStorage, self).__init__()

        self.parent = parent
        self.key = key

    @classmethod
    def open(cls, parent, key):
        storage = cls(parent, key)
        storage.initialize(parent._client)
        return storage

    def load(self, collection, media):
        try:
            data = self.main.database.get('item_key', (self.parent.source, self.parent.target, self.key), with_doc=True)
        except RecordNotFound:
            return None

        if 'doc' not in data:
            return None

        return ModelRegistry['Item'].from_dict(
            collection, data['doc'],
            media=media,
            storage=self
        )

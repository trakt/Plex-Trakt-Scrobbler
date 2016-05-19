from oem_framework.core.helpers import timestamp_utc
from oem_framework.models.core import Model


class Metadata(Model):
    __slots__ = ['collection', 'key', 'created_at', 'updated_at', 'hashes', 'media']

    def __init__(self, collection, key, storage, created_at=None, updated_at=None, hashes=None, media=None):
        self.collection = collection
        self.key = key
        self.storage = storage

        self.created_at = created_at
        self.updated_at = updated_at

        self.hashes = hashes or {}
        self.media = media

        if self.created_at is None:
            now = timestamp_utc()

            # Set initial timestamps
            self.created_at = now
            self.updated_at = now

    @property
    def index(self):
        return self.collection.index

    def to_dict(self):
        return {
            'created_at': self.created_at,
            'updated_at': self.updated_at,

            'hashes': self.hashes,
            'media': self.media
        }

    @classmethod
    def from_dict(cls, collection, data, key=None, storage=None):
        return cls(
            collection, key, storage,
            data.get('created_at'),
            data.get('updated_at'),

            data.get('hashes'),
            data.get('media')
        )

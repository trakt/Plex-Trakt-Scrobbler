from oem_framework.models.core import Model

import logging
import six

log = logging.getLogger(__name__)


class Index(Model):
    def __init__(self, collection, storage, items=None):
        self.collection = collection
        self.storage = storage

        self.items = items or {}

    @classmethod
    def from_dict(cls, collection, data, storage=None, **kwargs):
        index = cls(collection, storage)

        # Update index with items
        if data and 'items' in data:
            index.items = dict([
                (key, storage.parse(collection, key, value))
                for key, value in six.iteritems(data['items'])
            ])

        return index

    def to_dict(self):
        return {
            'items': dict([
                (key, item.to_dict())
                for key, item in self.items.items()
            ])
        }

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        return str(key) in self.items or key in self.items

    def __getitem__(self, key):
        return self.storage.get(self, key)

    def __setitem__(self, key, value):
        self.items[str(key)] = value

    def __repr__(self):
        source = self.collection.source
        target = self.collection.target

        if source and target:
            return '<Index %s -> %s (%r)>' % (
                source,
                target,
                self.storage
            )

        return '<Index %s (%r)>' % (
            source or target,
            self.storage
        )

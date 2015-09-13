from stash.caches.core.base import Cache
from stash.lib import six as six


class MemoryCache(Cache):
    __key__ = 'memory'

    def __init__(self, initial=None):
        super(MemoryCache, self).__init__()

        self.data = initial or {}

    def iteritems(self):
        return self.data.iteritems()

    def items(self):
        return self.data.items()

    def __delitem__(self, key):
        del self.data[key]

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __setitem__(self, key, value):
        self.data[key] = value

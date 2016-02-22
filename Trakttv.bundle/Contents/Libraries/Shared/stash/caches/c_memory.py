from stash.caches.core.base import Cache
from stash.core.exclusive import operation
from stash.lib.six import PY3


class MemoryCache(Cache):
    __key__ = 'memory'

    def __init__(self, initial=None):
        super(MemoryCache, self).__init__()

        self.data = initial or {}

    @operation()
    def iteritems(self):
        if PY3:
            return self.data.items()

        return self.data.iteritems()

    @operation()
    def items(self):
        return self.data.items()

    @operation()
    def __delitem__(self, key):
        del self.data[key]

    @operation()
    def __getitem__(self, key):
        return self.data[key]

    @operation()
    def __iter__(self):
        return iter(self.data)

    @operation()
    def __len__(self):
        return len(self.data)

    @operation()
    def __setitem__(self, key, value):
        self.data[key] = value

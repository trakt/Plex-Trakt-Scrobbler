from stash.algorithms.core.base import Algorithm
from stash.algorithms.core.prime_context import PrimeContext
from stash.core.helpers import to_integer
from stash.lib.six.moves import xrange, _thread

try:
    from llist import dllist
except ImportError:
    from pyllist import dllist

import collections
import logging

log = logging.getLogger(__name__)


class LruAlgorithm(Algorithm):
    __key__ = 'lru'

    def __init__(self, capacity=100, compact='auto', compact_threshold=200):
        super(LruAlgorithm, self).__init__()

        self.capacity = to_integer(capacity, 100)

        self.compact_mode = compact
        self.compact_threshold = to_integer(compact_threshold, 200)

        self.queue = dllist()
        self.nodes = {}

        self._buffers = {}

    def __delitem__(self, key):
        try:
            node = self.nodes.pop(key)

            # Remove `node` from `queue`
            self.queue.remove(node)
        except KeyError:
            pass

        # Remove `key` from `cache` and `archive`
        return super(LruAlgorithm, self).__delitem__(key)

    def __getitem__(self, key):
        # Try retrieve value from `prime_buffer`
        try:
            buffer = self._buffers.get(_thread.get_ident())

            if buffer is not None:
                return buffer[key]
        except KeyError:
            pass

        # Try retrieve value from `cache`
        try:
            value = self.cache[key]

            # Ensure node for `key` exists
            self.create(key)

            return value
        except KeyError:
            pass

        # Try load `key` from `archive`
        return self.load(key)

    def __setitem__(self, key, value):
        # Store `value` in cache
        self.cache[key] = value

        # Create node for `key`
        self.create(key)

    def compact(self, force=False):
        count = len(self.nodes)

        if count <= self.capacity:
            return

        if not force and count <= self.compact_threshold:
            return

        self.release_items(count - self.capacity)

    def delete(self, keys):
        if not keys:
            return

        if not isinstance(keys, collections.Iterable):
            keys = [keys]

        for key in keys:
            try:
                node = self.nodes.pop(key)

                # Remove `node` from `queue`
                self.queue.remove(node)
            except KeyError:
                pass

        # Remove keys from `cache` and `archive`
        return super(LruAlgorithm, self).delete(keys)

    def release(self, key=None):
        if key is None:
            key = self.queue.popright()

        # Move item to archive
        self.archive[key] = self.cache.pop(key)

        # Remove from `nodes`
        del self.nodes[key]

    def release_items(self, count=None, keys=None):
        if count is not None:
            def iterator():
                for x in xrange(count):
                    # Pop next item from `queue`
                    key = self.queue.popright()

                    # Delete from `nodes`
                    del self.nodes[key]

                    # Yield item
                    yield key, self.cache.pop(key)
        elif keys is not None:
            def iterator():
                for key in keys:
                    # Remove from `queue
                    self.queue.remove(key)

                    # Delete from `nodes`
                    del self.nodes[key]

                    # Yield item
                    yield key, self.cache.pop(key)
        else:
            raise ValueError()

        self.archive.set_items(iterator())
        return True

    def prime(self, keys=None, force=False):
        if keys is not None:
            # Filter keys to ensure we only load ones that don't exist
            keys = [
                key for key in keys
                if key not in self.cache
            ]

        # Iterate over archive items
        items = self.archive.get_items(keys)

        buffer = {}
        context = PrimeContext(self, buffer)

        for key, value in items:
            # Store `value` in cache
            buffer[key] = value

        return context

    def create(self, key, compact=True):
        if key in self.nodes:
            # Move node to the front of `queue`
            self.touch(key)
            return

        # Store node in `queue`
        self.nodes[key] = self.queue.appendleft(key)

        # Compact `cache` (if enabled)
        if compact and self.compact_mode == 'auto':
            self.compact()

    def load(self, key):
        # Load `key` from `archive`
        self[key] = self.archive[key]

        return self.cache[key]

    def touch(self, key):
        node = self.nodes[key]

        # Remove `node` from `queue`
        self.queue.remove(node)

        # Append `node` to the start of `queue`
        self.nodes[key] = self.queue.appendleft(node)

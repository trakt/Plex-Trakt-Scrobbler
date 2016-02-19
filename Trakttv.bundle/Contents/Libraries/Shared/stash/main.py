from stash.core.modules.manager import ModuleManager

from collections import MutableMapping
from threading import Lock


class Stash(MutableMapping):
    def __init__(self, archive, algorithm='lru:///', serializer='none:///', cache='memory:///', key_transform=None):
        # Construct modules
        self.archive = ModuleManager.construct(self, 'archive', archive)
        self.algorithm = ModuleManager.construct(self, 'algorithm', algorithm)
        self.serializer = ModuleManager.construct(self, 'serializer', serializer)
        self.cache = ModuleManager.construct(self, 'cache', cache)

        self.key_transform = key_transform or (lambda key: key, lambda key: key)

        self._flushing = Lock()

    def compact(self, force=False):
        return self.algorithm.compact(force=force)

    def delete(self, keys):
        return self.algorithm.delete(keys)

    def flush(self, force=False):
        if force:
            # Wait until flush can be started
            self._flushing.acquire()
        elif not self._flushing.acquire(False):
            # Flush already running
            return False

        try:
            # Take exclusive access of cache
            with self.cache.exclusive:
                # Update `archive` with the items in `cache`
                self.archive.update(self.cache.iteritems(__force=True))

            # Flush complete
            return True
        finally:
            self._flushing.release()

    def items(self):
        self.flush()

        return self.archive.items()

    def iteritems(self):
        self.flush()

        return self.archive.iteritems()

    def iterkeys(self):
        self.flush()

        return self.archive.iterkeys()

    def itervalues(self):
        self.flush()

        return self.archive.itervalues()

    def prime(self, keys=None, force=False):
        """Prime cache with `keys` from archive.

        :param keys: list of keys to load, or `None` to load everything
        :type keys: list of any or None

        :param force: force the loading of items (by ignoring the algorithm capacity parameter).
                      **Note:** these items will be removed on the next `compact()` call.
        :type force: bool
        """
        return self.algorithm.prime(
            keys=keys,
            force=force
        )

    def save(self):
        # Flush items from `cache` to `archive`
        self.flush()

        # Ensure `archive` is completely saved
        self.archive.save()

    def __delitem__(self, key):
        del self.algorithm[key]

    def __getitem__(self, key):
        return self.algorithm[key]

    def __iter__(self):
        self.flush()

        return iter(self.archive)

    def __len__(self):
        self.flush()

        return len(self.archive)

    def __setitem__(self, key, value):
        self.algorithm[key] = value

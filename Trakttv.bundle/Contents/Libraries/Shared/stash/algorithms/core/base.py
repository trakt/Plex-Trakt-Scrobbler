from stash.core.modules.base import Module


class Algorithm(Module):
    __group__ = 'algorithm'

    @property
    def archive(self):
        return self.stash.archive

    @property
    def cache(self):
        return self.stash.cache

    def compact(self, force=False):
        raise NotImplementedError

    def prime(self, keys=None, force=False):
        raise NotImplementedError

    def __delitem__(self, key):
        success = False

        try:
            # Delete `key` from `archive`
            del self.archive[key]
            success = True
        except KeyError:
            pass

        try:
            # Delete `key` from `cache`
            del self.cache[key]
            success = True
        except KeyError:
            pass

        if not success:
            # Couldn't find `key` in `archive` or `cache`
            raise KeyError(key)

    def __getitem__(self, key):
        try:
            return self.cache[key]
        except KeyError:
            # Load item into `cache`
            self.cache[key] = self.archive[key]

            return self.cache[key]

    def __setitem__(self, key, value):
        self.cache[key] = value

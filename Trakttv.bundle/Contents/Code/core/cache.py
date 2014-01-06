from core.eventing import EventHandler


class CacheItem(object):
    def __init__(self):
        self.invalidated = False


class Cache(object):
    def __init__(self, key):
        self.key = key
        self.data_store = {}

        self.on_refresh = EventHandler('%s.on_refresh' % key)

    def exists(self, key):
        return self.validate(key)

    def get(self, key, default=None, refresh=False):
        if not self.validate(key, refresh):
            return default

        return self.data_store[key]

    def validate(self, key, refresh=False):
        if key not in self.data_store:
            return False

        # TODO validate

    def invalidate(self, key, refresh=False):
        if key not in self.data_store:
            return

        self.data_store[key].invalidated = True

        if refresh:
            self.refresh(key)

    def refresh(self, key):
        pass

    def remove(self, key):
        self.data_store.pop(key)

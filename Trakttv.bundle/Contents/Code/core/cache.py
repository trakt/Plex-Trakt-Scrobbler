from core.eventing import EventHandler
from core.logger import Logger


log = Logger('core.cache')


class CacheItem(object):
    def __init__(self):
        self.invalidated = False
        self.data = None


class Cache(object):
    def __init__(self, key):
        self.key = key
        self.data_store = {}

        self.on_refresh = EventHandler('%s.on_refresh' % key)

    def exists(self, key):
        return self.is_valid(key)

    def get(self, key, default=None, refresh=False, create=True):
        if not self.is_valid(key):
            # Refresh and return data if successful
            if refresh and self.invalidate(key, refresh, create):
                return self.data_store[key].data

            return default

        log.debug('Returned cached %s for key %s', self.key, repr(key))
        return self.data_store[key].data

    def is_valid(self, key):
        if key not in self.data_store:
            return False

        return not self.data_store[key].invalidated

    def invalidate(self, key, refresh=False, create=False):
        if key not in self.data_store:
            if not create:
                return False

            self.data_store[key] = CacheItem()

        self.data_store[key].invalidated = True

        return self.refresh(key) if refresh else True

    def refresh(self, key):
        log.debug('Refreshing %s cache for key %s', self.key, repr(key))
        data = self.on_refresh.fire(key, single=True)
        if not data:
            return False

        self.data_store[key].data = data
        self.data_store[key].invalidated = False

        return True

    def remove(self, key):
        if key not in self.data_store:
            return

        self.data_store.pop(key)

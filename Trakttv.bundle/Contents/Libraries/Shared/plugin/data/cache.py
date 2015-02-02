from threading import Lock


class DataCache(object):
    def __init__(self):
        self.groups = {}
        self.lock = Lock()

    def __getitem__(self, key):
        if type(key) is not str:
            raise TypeError('Expecting a string for "key", instead got %s', type(key))

        # Normalize `key`
        key = key.lower()

        if key in self.groups:
            # Try retrieve directly
            return self.groups[key]

        # Acquire the lock and create a new group (if one doesn't exist)
        with self.lock:
            if key not in self.groups:
                self.groups[key] = DataCacheGroup()

            return self.groups[key]


class DataCacheGroup(object):
    def __init__(self):
        self.objects = {}
        self.lock = Lock()

    def delete(self, key):
        key = self._normalize_key(key)

        with self.lock:
            if key in self.objects:
                del self.objects[key]
                return True

            return False

    def get(self, key, default=None):
        key = self._normalize_key(key)

        with self.lock:
            return self.objects.get(key, default)

    def __getitem__(self, key):
        key = self._normalize_key(key)

        with self.lock:
            return self.objects[key]

    def __setitem__(self, key, value):
        key = self._normalize_key(key)

        with self.lock:
            self.objects[key] = value

    @staticmethod
    def _normalize_key(value):
        value = str(value)

        return value.lower()

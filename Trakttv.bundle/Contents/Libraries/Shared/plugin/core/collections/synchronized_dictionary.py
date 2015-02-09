from collections import MutableMapping
from threading import RLock


class SynchronizedDictionary(MutableMapping):
    def __init__(self, initial=None):
        self.store = initial or {}

        self.lock = RLock()

    def get(self, key, default=None, store=False):
        if key in self.store:
            return self.store[key]

        if not store:
            return default

        with self.lock:
            if key not in self.store:
                self.store[key] = default

            return self.store[key]

    def copy(self):
        return SynchronizedDictionary(self.store.copy())

    def __delitem__(self, key):
        with self.lock:
            del self.store[key]

    def __getitem__(self, key):
        with self.lock:
            return self.store[key]

    def __iter__(self):
        with self.lock:
            return iter(self.store)

    def __len__(self):
        with self.lock:
            return len(self.store)

    def __setitem__(self, key, value):
        with self.lock:
            self.store[key] = value

    def __repr__(self):
        return repr(self.store)

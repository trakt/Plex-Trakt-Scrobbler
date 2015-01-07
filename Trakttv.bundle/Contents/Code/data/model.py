from plugin.core.environment import Environment
from core.logger import Logger

import jsonpickle
import os

log = Logger('data.model')

cache = {}


class Model(object):
    group = None

    def __init__(self, key):
        self.key = key

    def save(self):
        if not self.group:
            raise ValueError()

        # Save to memory cache
        if self.group not in cache:
            cache[self.group] = {}

        cache[self.group][self.key] = self

        # Save to disk
        if not os.path.exists(self.group_path()):
            os.makedirs(self.group_path())

        Data.Save(self.item_path(self.key), jsonpickle.encode(self))

    @classmethod
    def all(cls, filter=None):
        if not cls.group or not os.path.exists(cls.group_path()):
            return []

        items = []

        for name in os.listdir(cls.group_path()):
            key, ext = os.path.splitext(name)

            if ext != '.json':
                continue

            value = cls.load(key)

            if filter and not filter(value):
                continue

            items.append((key, value))

        return items

    @classmethod
    def load(cls, key):
        if not cls.group:
            raise ValueError()

        # Try retrieve from memory cache
        if cls.group in cache and key in cache[cls.group]:
            return cache[cls.group][key]

        # Otherwise, try retrieve from disk
        if not os.path.exists(cls.group_path()):
            os.makedirs(cls.group_path())

        path = cls.item_path(key)

        if not Data.Exists(path):
            return None

        # Load data from disk
        try:
            data = Data.Load(path)
        except Exception, ex:
            log.warn('Unable to load "%s" (%s)', path, ex)
            return None

        # Decode data with jsonpickle
        item = None

        try:
            item = jsonpickle.decode(data)
        except Exception, ex:
            log.warn('Unable to decode "%s" (%s) - len(data): %s', path, ex, len(data) if data else None)
            return None

        # Cache item in memory
        if cls.group not in cache:
            cache[cls.group] = {}

        cache[cls.group][key] = item

        return item

    def delete(self):
        if not self.group:
            raise ValueError()

        # Delete from memory cache
        if self.group in cache and self.key in cache[self.group]:
            del cache[self.group][self.key]

        # Delete from disk
        if not os.path.exists(self.group_path()):
            os.makedirs(self.group_path())

        path = self.item_path(self.key)

        if not Data.Exists(path):
            return

        Data.Remove(path)

    @classmethod
    def group_path(cls):
        return os.path.join(Environment.path.plugin_data, cls.group)

    @classmethod
    def item_path(cls, key):
        if type(key) is tuple:
            key = '.'.join(key)

        return os.path.join(cls.group_path(), '%s.json' % key)

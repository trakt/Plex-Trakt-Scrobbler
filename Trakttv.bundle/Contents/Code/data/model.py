from plugin.core.environment import Environment
from core.logger import Logger

import jsonpickle
import os

log = Logger('data.model')


class Model(object):
    group = None

    def __init__(self, key):
        self.key = key

    def save(self):
        if not self.group:
            raise ValueError()

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

        if not os.path.exists(cls.group_path()):
            os.makedirs(cls.group_path())

        path = cls.item_path(key)

        if not Data.Exists(path):
            return None

        # Try load data from disk
        try:
            data = Data.Load(path)
        except Exception, ex:
            log.warn('Unable to load "%s" (%s)', path, ex)
            return None

        # Try decode data with jsonpickle
        try:
            return jsonpickle.decode(data)
        except Exception, ex:
            log.warn('Unable to decode "%s" (%s) - len(data): %s', path, ex, len(data) if data else None)
            return None

    def delete(self):
        if not self.group:
            raise ValueError()

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

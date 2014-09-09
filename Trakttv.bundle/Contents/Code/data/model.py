from core.logger import Logger
from core.plugin import PLUGIN_IDENTIFIER

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
        if not cls.group:# or cls.group not in Dict:
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

        data = Data.Load(path)
        log.debug('Data.Load(%r): %r', path, data)

        return jsonpickle.decode(data)

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
        return os.path.join(cls.data_path(), cls.group)

    @classmethod
    def item_path(cls, key):
        return os.path.join(cls.group_path(), '%s.json' % key)

    @classmethod
    def support_path(cls):
        code_path = Core.code_path
        base_path = code_path[:code_path.index(os.path.sep + 'Plug-ins')]

        return os.path.join(base_path, 'Plug-in Support')

    @classmethod
    def data_path(cls):
        return os.path.join(cls.support_path(), 'Data', PLUGIN_IDENTIFIER)

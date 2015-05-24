from stash.core.modules.base import MappingModule

import collections


class Archive(MappingModule):
    __group__ = 'archive'

    @property
    def serializer(self):
        return self.stash.serializer

    def dumps(self, value):
        return self.serializer.dumps(value)

    def loads(self, value):
        return self.serializer.loads(value)

    def save(self):
        raise NotImplementedError

    def delete(self, keys):
        if not keys:
            return

        if not isinstance(keys, collections.Iterable):
            keys = [keys]

        for key in keys:
            del self[key]

    def get_items(self, keys=None):
        if keys is None:
            return self.iteritems()

        return [(key, self[key]) for key in keys]

    def set_items(self, items):
        for key, value in items:
            self[key] = value

    def __delitem__(self, key):
        raise NotImplementedError

    def __getitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __setitem__(self, key, value):
        raise NotImplementedError

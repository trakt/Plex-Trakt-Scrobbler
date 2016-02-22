from stash.core.exclusive import ExclusiveContext
from stash.core.modules.base import MappingModule

import collections


class Cache(MappingModule):
    __group__ = 'cache'

    def __init__(self):
        super(Cache, self).__init__()

        self.exclusive = ExclusiveContext()

    def delete(self, keys):
        if not keys:
            return

        if not isinstance(keys, collections.Iterable):
            keys = [keys]

        for key in keys:
            del self[key]

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

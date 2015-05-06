# -*- coding: utf-8 -*-
'''
LevelDB database store.

shove's URI for LevelDB stores follows the form:

leveldb://<path>

Where <path> is a URL path to a LevelDB database. Alternatively, the native
pathname to a LevelDB database can be passed as the 'engine' parameter.
'''

try:
    import leveldb
except ImportError:
    raise ImportError('requires py-leveldb library')

from shove.store import ClientStore

__all__ = ['LevelDBStore']


class LevelDBStore(ClientStore):

    '''
    LevelDB-based object storage frontend.
    '''

    init = 'leveldb://'

    def __init__(self, engine, **kw):
        super(LevelDBStore, self).__init__(engine, **kw)
        self._store = leveldb.LevelDB(self._engine)

    def __getitem__(self, key):
        item = self.loads(self._store.Get(key), key)
        if item is not None:
            return item
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._store.Put(key, self.dumps(value))

    def __delitem__(self, key):
        self._store.Delete(key)

    def __iter__(self):
        return self._store.RangeIter(include_value=False)

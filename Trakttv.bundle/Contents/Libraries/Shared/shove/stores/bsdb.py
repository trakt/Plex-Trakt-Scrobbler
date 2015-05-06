# -*- coding: utf-8 -*-
'''
Berkeley Source Database Store.

shove's URI for BSDDB stores follows the form:

bsddb://<path>

Where the path is a URL path to a Berkeley database. Alternatively, the native
pathname to a Berkeley database can be passed as the 'engine' parameter.
'''

from threading import Condition

from stuf.six import b
try:
    from bsddb import hashopen
except ImportError:
    try:
        from bsddb3 import hashopen
    except ImportError:
        raise ImportError('requires bsddb library')

from shove.store import SyncStore
from shove._compat import synchronized

__all__ = ['BSDBStore']


class BSDBStore(SyncStore):

    '''Berkeley Source Database-based object storage frontend.'''

    init = 'bsddb://'

    def __init__(self, engine, **kw):
        super(BSDBStore, self).__init__(engine, **kw)
        self._store = hashopen(self._engine)
        self._lock = Condition()
        self.sync = self._store.sync

    @synchronized
    def __getitem__(self, key):
        return self.loads(self._store[key], key)

    @synchronized
    def __setitem__(self, key, value):
        self._store[b(key)] = self.dumps(value)
        self.sync()

    @synchronized
    def __delitem__(self, key):
        del self._store[b(key)]
        self.sync()

# -*- coding: utf-8 -*-
'''shove store support.'''

import shutil
from copy import deepcopy
from threading import Condition
from collections import MutableMapping

from shove.base import Mapping, FileBase
from shove._compat import anydbm, synchronized, url2pathname

__all__ = 'DBMStore FileStore MemoryStore SimpleStore'.split()


class BaseStore(Mapping, MutableMapping):

    '''Base store.'''

    def close(self):
        '''Closes internal store and clears object references.'''
        try:
            self._store.close()
        except AttributeError:
            pass
        self._store = None


class SimpleStore(BaseStore):

    '''
    Single-process in-memory store.

    The shove URI for a simple store is:

    simple://
    '''

    def __init__(self, engine, **kw):
        super(SimpleStore, self).__init__(engine, **kw)
        self._store = dict()


class MemoryStore(SimpleStore):

    '''
    Thread-safe in-memory store.

    The shove URI for a memory store is:

    memory://
    '''

    def __init__(self, engine, **kw):
        super(MemoryStore, self).__init__(engine, **kw)
        self._lock = Condition()

    @synchronized
    def __getitem__(self, key):
        return deepcopy(super(MemoryStore, self).__getitem__(key))

    __setitem__ = synchronized(SimpleStore.__setitem__)
    __delitem__ = synchronized(SimpleStore.__delitem__)


class ClientStore(BaseStore):

    '''Base store where updates must be committed to disk.'''

    def __init__(self, engine, **kw):
        super(ClientStore, self).__init__(engine, **kw)
        if engine.startswith(self.init):
            self._engine = url2pathname(engine.split('://')[1])

    def __getitem__(self, key):
        return self.loads(super(ClientStore, self).__getitem__(key))

    def __setitem__(self, key, value):
        super(ClientStore, self).__setitem__(key, self.dumps(value))


class SyncStore(ClientStore):

    '''Base store where updates have to be synced to disk.'''

    def __setitem__(self, key, value):
        super(SyncStore, self).__setitem__(key, value)
        try:
            self.sync()
        except AttributeError:
            pass

    def __delitem__(self, key):
        super(SyncStore, self).__delitem__(key)
        try:
            self.sync()
        except AttributeError:
            pass


class DBMStore(SyncStore):

    '''
    DBM Database Store.

    shove's URI for DBM stores follows the form:

    dbm://<path>

    Where <path> is a URL path to a DBM database. Alternatively, the native
    pathname to a DBM database can be passed as the 'engine' parameter.
    '''

    init = 'dbm://'

    def __init__(self, engine, **kw):
        super(DBMStore, self).__init__(engine, **kw)
        self._store = anydbm.open(self._engine, 'c')
        try:
            self.sync = self._store.sync
        except AttributeError:
            pass

    def __iter__(self):
        return iter(self._store.keys())


class FileStore(FileBase, BaseStore):

    '''
    Filesystem-based object store.

    shove's URI for filesystem-based stores follows the form:

    file://<path>

    Where the path is a URI path to a directory on a local filesystem.
    Alternatively, a native pathname to the directory can be passed as the
    'engine' argument.
    '''

    init = 'file://'

    def clear(self):
        '''Clear all objects from store.'''
        shutil.rmtree(self._dir)
        self._createdir()

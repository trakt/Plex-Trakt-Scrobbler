# -*- coding: utf-8 -*-
'''shove cache core.'''

from time import time
from copy import deepcopy
from operator import delitem
from collections import deque
from random import seed, sample
from threading import Condition

from stuf.iterable import xpartmap

from shove._compat import synchronized
from shove.base import Mapping, FileBase


__all__ = (
    'FileCache FileLRUCache MemoryCache SimpleCache MemoryLRUCache'
    'SimpleLRUCache'
).split()


class BaseCache(object):

    def __init__(self, engine, **kw):
        super(BaseCache, self).__init__(engine, **kw)
        # get random seed
        seed()
        # set maximum number of items to cull if over max
        self._maxcull = kw.get('maxcull', 10)
        # set max entries
        self._max_entries = kw.get('max_entries', 300)
        # set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        exp, value = super(BaseCache, self).__getitem__(key)
        # delete if item timed out.
        if exp < time():
            super(BaseCache, self).__delitem__(key)
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        # set expiration time and value
        exp = time() + self.timeout
        super(BaseCache, self).__setitem__(key, (exp, value))
        # cull values if over max number of entries
        if len(self) > self._max_entries:
            self._cull()

    def _cull(self):
        # cull remainder of allowed quota at random
        xpartmap(
            delitem, sample(list(self), len(self) - self._max_entries), self
        )


class SimpleCache(BaseCache, Mapping):

    '''
    Single-process in-memory cache.

    The shove URI for a simple cache is:

    simple://
    '''

    def __init__(self, engine, **kw):
        super(SimpleCache, self).__init__(engine, **kw)
        self._store = dict()


class MemoryCache(SimpleCache):

    '''
    Thread-safe in-memory cache.

    The shove URI for a memory cache is:

    memory://
    '''

    def __init__(self, engine, **kw):
        super(MemoryCache, self).__init__(engine, **kw)
        self._lock = Condition()

    @synchronized
    def __getitem__(self, key):
        return deepcopy(super(MemoryCache, self).__getitem__(key))

    __setitem__ = synchronized(SimpleCache.__setitem__)
    __delitem__ = synchronized(SimpleCache.__delitem__)


class FileCache(BaseCache, FileBase):

    '''
    File-based cache

    shove's URI for file caches follows the form:

    file://<path>

    Where the path is a URI path to a directory on a local filesystem.
    Alternatively, a native pathname to the directory can be passed as the
    'engine' argument.
    '''

    init = 'file://'

    def __init__(self, engine, **kw):
        super(FileCache, self).__init__(engine, **kw)

    def __getitem__(self, key):
        try:
            exp, value = super(FileCache, self).__getitem__(key)
            # remove item if time has expired.
            if exp < time():
                del self[key]
                raise KeyError(key)
            return value
        except:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if len(self) >= self._max_entries:
            self._cull()
        super(FileCache, self).__setitem__(key, (time() + self.timeout, value))


class BaseLRUCache(BaseCache):

    def __init__(self, engine, **kw):
        super(BaseLRUCache, self).__init__(engine, **kw)
        self._max_entries = kw.get('max_entries', 300)
        self._hits = 0
        self._misses = 0
        self._queue = deque()
        self._refcount = dict()

    def __getitem__(self, key):
        try:
            value = super(BaseLRUCache, self).__getitem__(key)
            self._hits += 1
        except KeyError:
            self._misses += 1
            raise
        self._housekeep(key)
        return value

    def __setitem__(self, key, value):
        super(BaseLRUCache, self).__setitem__(key, value)
        self._housekeep(key)
        if len(self) > self._max_entries:
            queue = self._queue
            store = self
            max_entries = self._max_entries
            refcount = self._refcount
            ditem = super(BaseLRUCache, self).__delitem__
            qpopleft = queue.popleft
            while len(store) > max_entries:
                k = qpopleft()
                refcount[k] -= 1
                if not refcount[k]:
                    ditem(k)
                    del refcount[k]

    def _housekeep(self, key):
        self._queue.append(key)
        self._refcount[key] = self._refcount.get(key, 0) + 1
        if len(self._queue) > self._max_entries * 4:
            queue = self._queue
            qpopleft, qappend = queue.popleft, queue.append
            refcount = self._refcount
            for _ in [None] * len(queue):
                k = qpopleft()
                if refcount[k] == 1:
                    qappend(k)
                else:
                    refcount[k] -= 1


class SimpleLRUCache(BaseLRUCache, Mapping):

    '''
    Single-process in-memory LRU cache that purges based on least recently
    used item.

    The shove URI for a simple cache is:

    simplelru://
    '''

    def __init__(self, engine, **kw):
        super(SimpleLRUCache, self).__init__(engine, **kw)
        self._store = dict()


class MemoryLRUCache(SimpleLRUCache):

    '''
    Thread-safe in-memory cache using LRU.

    The shove URI for a memory cache is:

    memlru://
    '''

    def __init__(self, engine, **kw):
        super(MemoryLRUCache, self).__init__(engine, **kw)
        self._lock = Condition()

    @synchronized
    def __getitem__(self, key):
        return deepcopy(super(MemoryLRUCache, self).__getitem__(key))

    __setitem__ = synchronized(SimpleLRUCache.__setitem__)
    __delitem__ = synchronized(SimpleLRUCache.__delitem__)


class FileLRUCache(BaseLRUCache, FileBase):

    '''
    File-based LRU cache

    shove's URI for file caches follows the form:

    filelru://<path>

    Where the path is a URI path to a directory on a local filesystem.
    Alternatively, a native pathname to the directory can be passed as the
    'engine' argument.
    '''

    init = 'filelru://'

    def __init__(self, engine, **kw):
        super(FileLRUCache, self).__init__(engine, **kw)

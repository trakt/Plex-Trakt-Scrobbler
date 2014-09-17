# -*- coding: utf-8 -*-
'''shove core.'''

from operator import methodcaller
from collections import MutableMapping

from stuf import exhaustmap
from stuf.iterable import xpartmap
from concurrent.futures import ThreadPoolExecutor

from shove._imports import cache_backend, store_backend

__all__ = 'Shove MultiShove'.split()


class Shove(MutableMapping):

    '''Common object frontend class.'''

    def __init__(self, store='simple://', cache='simple://', **kw):
        super(Shove, self).__init__()
        # load store backend
        self._store = store_backend(store, **kw)
        # load cache backend
        self._cache = cache_backend(cache, **kw)
        # buffer for lazier writing
        self._buffer = dict()
        # setting for syncing frequency
        self._sync = kw.get('sync', 2)

    def __getitem__(self, key):
        try:
            return self._cache[key]
        except KeyError:
            # synchronize cache with store
            self.sync()
            self._cache[key] = value = self._store[key]
            return value

    def __setitem__(self, key, value):
        self._cache[key] = self._buffer[key] = value
        # when buffer reaches self._limit, write buffer to store
        if len(self._buffer) >= self._sync:
            self.sync()

    def __delitem__(self, key):
        self.sync()
        try:
            del self._cache[key]
        except KeyError:
            pass
        del self._store[key]

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        self.sync()
        return self._store.__iter__()

    def close(self):
        '''Finalizes and closes shove.'''
        # if close has been called, pass
        if self._store is not None:
            try:
                self.sync()
            except AttributeError:
                pass
            self._store.close()
        self._store = self._cache = self._buffer = None

    def sync(self):
        '''Writes buffer to store.'''
        self._store.update(self._buffer)
        self._buffer.clear()

    def clear(self):
        self._store.clear()
        self._buffer.clear()


class MultiShove(MutableMapping):

    '''Common frontend to multiple object stores.'''

    def __init__(self, *stores, **kw):
        # init superclass with first store
        super(MultiShove, self).__init__()
        if not stores:
            stores = ('simple://',)
        # load stores
        self._stores = list(store_backend(i, **kw) for i in stores)
        # load cache
        self._cache = cache_backend(kw.get('cache', 'simple://'), **kw)
        # buffer for lazy writing
        self._buffer = dict()
        # setting for syncing frequency
        self._sync = kw.get('sync', 2)

    def __getitem__(self, key):
        try:
            return self._cache[key]
        except KeyError:
            # synchronize cache and store
            self.sync()
            # get value from first store
            self._cache[key] = value = self._stores[0][key]
            return value

    def __setitem__(self, key, value):
        self._cache[key] = self._buffer[key] = value
        # when the buffer reaches self._limit, writes the buffer to the store
        if len(self._buffer) >= self._sync:
            self.sync()

    def __delitem__(self, key):
        try:
            self.sync()
        except AttributeError:
            pass
        exhaustmap(methodcaller('__delitem__', key), self._stores)
        try:
            del self._cache[key]
        except KeyError:
            pass

    def __len__(self):
        return len(self._stores[0])

    def __iter__(self):
        self.sync()
        return self._stores[0].__iter__()

    def close(self):
        '''Finalizes and closes shove stores.'''
        # if close has been called, pass
        stores = self._stores
        if self._stores is not None:
            self.sync()
            # close stores
            for idx, store in enumerate(stores):
                store.close()
                stores[idx] = None
        self._cache = self._buffer = self._stores = None

    def sync(self):
        '''Writes buffer to stores.'''
        exhaustmap(methodcaller('update', self._buffer), self._stores)
        self._buffer.clear()


class ThreadShove(MultiShove):

    '''Common frontend that syncs multiple object stores with threads.'''

    def __init__(self, *stores, **kw):
        # init superclass with first store
        super(ThreadShove, self).__init__(*stores, **kw)
        self._maxworkers = kw.get('max_workers', 2)

    def __delitem__(self, key):
        try:
            self.sync()
        except AttributeError:
            pass
        with ThreadPoolExecutor(max_workers=self._maxworkers) as executor:
            xpartmap(
                executor.submit,
                self._stores,
                methodcaller('__delitem__', key),
            )
        try:
            del self._cache[key]
        except KeyError:
            pass

    def sync(self):
        '''Writes buffer to store.'''
        with ThreadPoolExecutor(max_workers=self._maxworkers) as executor:
            xpartmap(
                executor.submit,
                self._stores,
                methodcaller('update', self._buffer),
            )
        self._buffer.clear()

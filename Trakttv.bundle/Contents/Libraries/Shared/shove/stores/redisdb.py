# -*- coding: utf-8 -*-
'''
Redis-based object store

The shove URI for a redis-based store is:

redis://<host>:<port>/<db>
'''

try:
    import redis
except ImportError:
    raise ImportError('requires the redis library')

from shove._compat import urlsplit

from shove.store import BaseStore

__all__ = ['RedisStore']


class RedisStore(BaseStore):

    '''Redis-based object storage frontend.'''

    init = 'redis://'

    def __init__(self, engine, **kw):
        super(RedisStore, self).__init__(engine, **kw)
        spliturl = urlsplit(engine)
        self._db = spliturl.path.replace('/', '')
        self._hostname = spliturl.hostname
        self._port = spliturl.port
        self._store = redis.Redis(spliturl.hostname, spliturl.port, self._db)

    def __contains__(self, key):
        return self._store.exists(key)

    def __len__(self):
        return len(self._store.keys())

    def clear(self):
        self._store.flushall()

    def __iter__(self):
        return iter(self._store.keys())

    def keys(self):
        return self._store.keys()

    def setdefault(self, key, default=None):
        return self._store.getset(key, default)

# -*- coding: utf-8 -*-
'''
Redis-based object cache

The shove URI for a redis cache is:

redis://<host>:<port>/<db>
'''

try:
    import redis
except ImportError:
    raise ImportError('requires redis')

from shove.base import Base
from shove._compat import urlsplit

__all__ = ['RedisCache']


class RedisCache(Base):

    '''Redis-based cache backend'''

    init = 'redis://'

    def __init__(self, engine, **kw):
        super(RedisCache, self).__init__(engine, **kw)
        spliturl = urlsplit(engine)
        host, port = spliturl[1].split(':')
        db = spliturl[2].replace('/', '')
        self._store = redis.Redis(host, int(port), db)
        # Set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        return self.loads(self._store[key], key)

    def __setitem__(self, key, value):
        self._store.setex(key, self.dumps(value), self.timeout)

    def __delitem__(self, key):
        self._store.delete(key)

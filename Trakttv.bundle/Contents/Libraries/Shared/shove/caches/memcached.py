# -*- coding: utf-8 -*-
'''
"memcached" cache.

The shove URI for a memcache cache is:

memcache://<memcache_server>
'''

try:
    import memcache
except ImportError:
    raise ImportError("requires 'python-memcached' library")

from shove.base import Base

__all__ = ['MemCache']


class MemCache(Base):

    '''Memcached-based cache frontend.'''

    def __init__(self, engine, **kw):
        super(MemCache, self).__init__(engine, **kw)
        if engine.startswith('memcache://'):
            engine = engine.split('://')[1]
        self._store = memcache.Client(engine.split(';'))
        # set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        value = self._store.get(key)
        if value is None:
            raise KeyError(key)
        return self.loads(value, key)

    def __setitem__(self, key, value):
        self._store.set(key, self.dumps(value), self.timeout)

    def __delitem__(self, key):
        self._store.delete(key)

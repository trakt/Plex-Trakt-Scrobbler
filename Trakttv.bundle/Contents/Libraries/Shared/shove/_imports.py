# -*- coding: utf-8 -*-
'''shove loadpoints.'''

from stuf.six import strings
from stuf.utils import lazyimport

try:
    from pkg_resources import iter_entry_points

    stores = dict(
        (_store.name, _store) for _store in iter_entry_points('shove.stores')
    )
    caches = dict(
        (_cache.name, _cache) for _cache in iter_entry_points('shove.caches')
    )
except ImportError:
    # `pkg_resources` not available, fallback to static map
    stores = {
        'bsddb'    : 'shove.stores.bsdb:BSDBStore',
        'cassandra': 'shove.stores.cassandra:CassandraStore',
        'dbm'      : 'shove.store:DBMStore',
        'durus'    : 'shove.stores.durusdb:DurusStore',
        'file'     : 'shove.store:FileStore',
        'firebird' : 'shove.stores.db:DBStore',
        'ftp'      : 'shove.stores.ftp:FTPStore',
        'hdf5'     : 'shove.stores.hdf5:HDF5Store',
        'leveldb'  : 'shove.stores.leveldbstore:LevelDBStore',
        'memory'   : 'shove.store:MemoryStore',
        'mongodb'  : 'shove.stores.mongodb:MongoDBStore',
        'mssql'    : 'shove.stores.db:DBStore',
        'mysql'    : 'shove.stores.db:DBStore',
        'oracle'   : 'shove.stores.db:DBStore',
        'postgres' : 'shove.stores.db:DBStore',
        'redis'    : 'shove.stores.redisdb:RedisStore',
        's3'       : 'shove.stores.s3:S3Store',
        'simple'   : 'shove.store:SimpleStore',
        'sqlite'   : 'shove.stores.db:DBStore',
        'zodb'     : 'shove.stores.zodb:ZODBStore',
        'hg'       : 'shove.stores.hgstore:HgStore',
        'git'      : 'shove.stores.gitstore:GitStore'
    }

    caches = {
        'file'     : 'shove.cache:FileCache',
        'filelru'  : 'shove.cache:FileLRUCache',
        'firebird' : 'shove.caches.db:DBCache',
        'memcache' : 'shove.caches.memcached:MemCache',
        'memlru'   : 'shove.cache:MemoryLRUCache',
        'memory'   : 'shove.cache:MemoryCache',
        'mssql'    : 'shove.caches.db:DBCache',
        'mysql'    : 'shove.caches.db:DBCache',
        'oracle'   : 'shove.caches.db:DBCache',
        'postgres' : 'shove.caches.db:DBCache',
        'redis'    : 'shove.caches.redisdb:RedisCache',
        'simple'   : 'shove.cache:SimpleCache',
        'simplelru': 'shove.cache:SimpleLRUCache',
        'sqlite'   : 'shove.caches.db:DBCache'
    }


def cache_backend(uri, **kw):
    '''
    Loads the right cache backend based on a URI.

    :argument uri: instance or name :class:`str`
    '''
    if isinstance(uri, strings):
        mod = caches[uri.split('://', 1)[0]]
        # load module if setuptools not present
        if isinstance(mod, strings):
            # split classname from dot path
            module, klass = mod.split(':')
            # load module
            mod = lazyimport(module, klass)
        # load appropriate class from setuptools entry point
        else:
            mod = mod.load()
        # return instance
        return mod(uri, **kw)
    # no-op for existing instances
    return uri


def store_backend(uri, **kw):
    '''
    Loads the right store backend based on a URI.

    :argument uri: instance or name :class:`str`
    '''
    if isinstance(uri, strings):
        mod = stores[uri.split('://', 1)[0]]
        # load module if setuptools not present
        if isinstance(mod, strings):
            # isolate classname from dot path
            module, klass = mod.split(':')
            # load module
            mod = lazyimport(module, klass)
        # load appropriate class from setuptools entry point
        else:
            mod = mod.load()
        # return instance
        return mod(uri, **kw)
    # no-op for existing instances
    return uri

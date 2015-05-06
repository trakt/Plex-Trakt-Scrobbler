# -*- coding: utf-8 -*-
'''
Cassandra-based object store

The shove URI for a cassandra-based store is:

cassandra://<host>:<port>/<keyspace>/<columnFamily>
'''

from stuf.six import native

try:
    import pycassa
except ImportError:
    raise ImportError('requires pycassa library')

from shove._compat import urlsplit
from shove.store import SimpleStore

__all__ = ['CassandraStore']


class CassandraStore(SimpleStore):

    '''Cassandra based storage frontend.'''

    init = 'cassandra://'

    def __init__(self, engine, **kw):
        super(CassandraStore, self).__init__(engine, **kw)
        spliturl = urlsplit(engine)
        _, keyspace, column_family = spliturl.path.split('/')
        try:
            self._store = pycassa.ColumnFamily(
                pycassa.ConnectionPool(keyspace, [spliturl.hostname]),
                column_family,
            )
        except pycassa.InvalidRequestException:
            from pycassa.system_manager import SystemManager  # @UnresolvedImport @IgnorePep8
            system_manager = SystemManager(spliturl[1])
            system_manager.create_keyspace(
                keyspace,
                pycassa.system_manager.SIMPLE_STRATEGY,
                dict(replication_factor=native(kw.get('replication', 1))),
            )
            system_manager.create_column_family(keyspace, column_family)
            self._store = pycassa.ColumnFamily(
                pycassa.ConnectionPool(keyspace, [spliturl.netloc]),
                column_family,
            )
        except pycassa.NotFoundException:
            from pycassa.system_manager import SystemManager  # @UnresolvedImport @IgnorePep8
            system_manager = SystemManager(spliturl[1])
            system_manager.create_column_family(keyspace, column_family)
            self._store = pycassa.ColumnFamily(
                pycassa.ConnectionPool(keyspace, [spliturl.netloc]),
                column_family,
            )

    def __getitem__(self, key):
        try:
            item = self._store.get(key).get('key')
            if item is not None:
                return self.loads(item, key)
            raise KeyError(key)
        except pycassa.NotFoundException:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._store.insert(key, dict(key=self.dumps(value)))

    def __delitem__(self, key):
        # beware eventual consistency
        try:
            self._store.remove(key)
        except pycassa.NotFoundException:
            raise KeyError(key)

    def __len__(self):
        return len(list(self._store.get_range()))

    def __iter__(self):
        for item in self._store.get_range():
            yield item[0]

    def clear(self):
        # beware eventual consistency
        self._store.truncate()

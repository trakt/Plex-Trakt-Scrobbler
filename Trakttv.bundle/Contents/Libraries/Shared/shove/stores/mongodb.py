# -*- coding: utf-8 -*-
'''
MongoDB database store.

shove's URI for MongoDB stores follows the form:

mongodb://<host>:<port>/<db>/collection/
'''

try:
    from bson.binary import Binary
    from pymongo.connection import Connection
except ImportError:
    raise ImportError('requires pymongo library')

from shove._compat import urlsplit
from shove.store import SimpleStore

__all__ = ['MongoDBStore']


class MongoDBStore(SimpleStore):

    '''MongoDB-based object storage frontend.'''

    init = 'mongodb://'

    def __init__(self, engine, **kw):
        super(MongoDBStore, self).__init__(engine, **kw)
        spliturl = urlsplit(engine)
        _, dbpath, self._colpath = spliturl.path.split('/')
        self._conn = Connection(host=spliturl.hostname, port=spliturl.port)
        self._db = getattr(self._conn, dbpath)
        self._store = getattr(self._db, self._colpath)
        self._store.ensure_index('key', unique=True)

    def __getitem__(self, key):
        try:
            return self.loads(self._store.find_one(dict(key=key))['value'])
        except TypeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        self._store.save(dict(key=key, value=Binary(self.dumps(value))))

    def __delitem__(self, key):
        self._store.remove(dict(key=key))

    def __len__(self):
        return self._store.count()

    def __iter__(self):
        for key in self._store.find(
            dict(key={'$exists': True}), fields=['key'],
        ):
            yield key['key']

    def close(self):
        self._conn.close()

    def clear(self):
        self._store.drop()
        self._store = getattr(self._db, self._colpath)

    def items(self):
        for key in self._store.find({'key': {'$exists': True}}):
            yield (key['key'], key['value'])

    def values(self):
        loads = self.loads
        for value in self._store.distinct('key'):
            yield loads(value['value'])

# -*- coding: utf-8 -*-
'''
Database object cache.

The shove URI used for database object caches is the format used by
SQLAlchemy:

<driver>://<username>:<password>@<host>:<port>/<database>

<driver> is the database engine. The engines currently supported SQLAlchemy are
sqlite, mysql, postgres, oracle, mssql, and firebird.
<username> is the database account user name
<password> is the database accound password
<host> is the database location
<port> is the database port
<database> is the name of the specific database

For more information on specific databases see:

http://www.sqlalchemy.org/docs/dbengine.myt#dbengine_supported
'''

import time
from random import sample
from datetime import datetime

from stuf.six import native
try:
    from sqlalchemy import LargeBinary as Binary
except ImportError:
    from sqlalchemy import Binary
try:
    from sqlalchemy import (
        MetaData, Table, Column, String, DateTime, select, update, insert,
        delete,
    )
except ImportError:
    raise ImportError('requires SQLAlchemy >= 0.4')

from shove.base import Base

__all__ = ['DBCache']


class DBCache(Base):

    '''Relational database-based cache frontend.'''

    def __init__(self, engine, **kw):
        super(DBCache, self).__init__(engine, **kw)
        # make cache table
        self._store = Table(
            # get table name
            kw.get('tablename', 'cache'),
            # bind metadata
            MetaData(engine),
            Column('key', String(60), primary_key=True, nullable=False),
            Column('value', Binary, nullable=False),
            Column('expires', DateTime, nullable=False),
        )
        # create cache table if it does not exist
        if not self._store.exists():
            self._store.create()
        # set maximum entries
        self._max_entries = kw.get('max_entries', 300)
        # maximum number of entries to cull per call if cache is full
        self._maxcull = kw.get('maxcull', 10)
        # set timeout
        self.timeout = kw.get('timeout', 300)

    def __getitem__(self, key):
        row = select(
             [self._store.c.value, self._store.c.expires],
            self._store.c.key == key
        ).execute().fetchone()
        if row is not None:
            # remove if item expired
            if row.expires < datetime.now().replace(microsecond=0):
                del self[key]
                raise KeyError(key)
            return self.loads(native(row.value), key)
        raise KeyError(key)

    def __setitem__(self, key, value):
        value = self.dumps(value)
        # cull if too many items
        if len(self) >= self._max_entries:
            self._cull()
        # generate expiration time
        expires = datetime.fromtimestamp(
            time.time() + self.timeout
        ).replace(microsecond=0)
        # update database if key already present
        if key in self:
            cache = self._store
            update(
                cache,
                cache.c.key == key,
                dict(value=value, expires=expires),
            ).execute()
        # insert new key if key not present
        else:
            insert(
                self._store, dict(key=key, value=value, expires=expires)
            ).execute()

    def __delitem__(self, key):
        self._store.delete(self._store.c.key == key).execute()

    def __iter__(self):
        for item in select([self._store.c.key]).execute().fetchall():
            yield item[0]

    def __len__(self):
        return self._store.count().execute().fetchone()[0]

    def _cull(self):
        # remove items in cache to make more room
        cache = self._store
        # remove items that have timed out
        delete(
            cache, cache.c.expires < datetime.now().replace(microsecond=0),
        ).execute()
        # remove any items over the maximum allowed number in the cache
        length = len(self)
        if length >= self._max_entries:
            cull = length if length < self._maxcull else self._maxcull
            # get list of keys
            keys = list(i[0] for i in select(
                [cache.c.key], limit=cull * 2
            ).execute().fetchall())
            # delete keys at random
            delete(cache, cache.c.key.in_(sample(keys, cull))).execute()

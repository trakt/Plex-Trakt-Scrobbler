# -*- coding: utf-8 -*-
'''
Relational database object store.

The shove URI used for relational database object stores is the format used by
SQLAlchemy:

<driver>://<username>:<password>@<host>:<port>/<database>

<driver> is the database engine
<username> is the database account user name
<password> is the database accound password
<host> is the database location
<port> is the database port
<database> is the name of the specific database

For more information on supported databases, see:

http://docs.sqlalchemy.org/en/rel_0_7/dialects/index.html
'''

from stuf.six import native
try:
    from sqlalchemy import LargeBinary as Binary
except ImportError:
    from sqlalchemy import Binary
try:
    from sqlalchemy import MetaData, Table, Column, String, select
except ImportError:
    raise ImportError('requires SQLAlchemy >= 0.4')

from shove.store import BaseStore

__all__ = ['DBStore']


class DBStore(BaseStore):

    '''Relational database-based object storage frontend.'''

    def __init__(self, engine, **kw):
        super(DBStore, self).__init__(engine, **kw)
        # make store table
        self._store = Table(
            # get tablename
            kw.get('tablename', 'store'),
            MetaData(engine),
            Column('key', String(255), primary_key=True, nullable=False),
            Column('value', Binary, nullable=False),
        )
        # create store table if it does not exist
        if not self._store.exists():
            self._store.create()

    def __getitem__(self, key):
        row = select(
            [self._store.c.value], self._store.c.key == key,
        ).execute().fetchone()
        if row is not None:
            return self.loads(native(row.value), key)
        raise KeyError(key)

    def __setitem__(self, k, v):
        v, store = self.dumps(v), self._store
        # update database if key already present
        if k in self:
            store.update(store.c.key == k).execute(value=v)
        # insert new key if key not present
        else:
            store.insert().execute(key=k, value=v)

    def __delitem__(self, key):
        self._store.delete(self._store.c.key == key).execute()

    def __iter__(self):
        for item in select([self._store.c.key]).execute().fetchall():
            yield item[0]

    def __len__(self):
        return self._store.count().execute().fetchone()[0]

    def clear(self):
        self._store.delete().execute()

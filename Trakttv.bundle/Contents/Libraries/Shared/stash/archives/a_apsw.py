from stash.archives.core.base import Archive
from stash.lib import six as six

from collections import Mapping
from contextlib import closing
import collections

try:
    import apsw
except ImportError:
    apsw = None

if six.PY3:
    def buffer(value):
        return value


class ApswArchive(Archive):
    __key__ = 'apsw'

    def __init__(self, db, table):
        super(ApswArchive, self).__init__()

        if apsw is None:
            raise Exception('Unable to construct apsw:// - "apsw" module is not available')

        self.db = apsw.Connection(db) if type(db) is str else db
        self.table = table

        # Ensure table exists
        with closing(self.db.cursor()) as c:
            c.execute('create table if not exists "%s" (key PRIMARY KEY, value BLOB)' % self.table)

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        rows = self.select('select key, value from "%s"' % self.table)

        for key, value in rows:
            yield self.key_decode(key), self.loads(value)

    def iterkeys(self):
        rows = self.select('select key from "%s"' % self.table)

        for key, in rows:
            yield self.key_decode(key)

    def itervalues(self):
        rows = self.select('select value from "%s"' % self.table)

        for value, in rows:
            yield self.loads(value)

    def keys(self):
        return list(self.iterkeys())

    def save(self):
        pass

    def select(self, sql, parameters=None):
        if parameters is None:
            parameters = ()

        with closing(self.db.cursor()) as c:
            return list(c.execute(sql, parameters))

    def select_one(self, sql, parameters=None):
        rows = self.select(sql, parameters)

        if not rows:
            return None

        return rows[0]

    def delete(self, keys):
        if not keys:
            return

        if not isinstance(keys, collections.Iterable):
            keys = [keys]

        # Create cursor
        with closing(self.db.cursor()) as c:
            # Delete `keys`
            c.executemany(self._query_delete(), [
                self.key_encode(key)
                for key in keys
            ])

    def get_items(self, keys=None):
        if keys:
            # encode keys
            keys = [
                self.key_encode(key)
                for key in keys
            ]

            rows = self.select('select key,value from "%s" where key in ?' % self.table, (keys,))
        else:
            rows = self.select('select key,value from "%s"' % self.table)

        for key, value in rows:
            yield self.key_decode(key), self.loads(value)

    def set_items(self, items):
        # Create cursor
        with closing(self.db.cursor()) as c:
            # Insert `items`
            c.executemany(self._query_upsert(), [
                (self.key_encode(key), buffer(self.dumps(value)))
                for key, value in items
            ])

    def update(self, *args, **kwds):
        if args:
            other = args[0]
            if isinstance(other, Mapping):
                if six.PY3:
                    self.set_items(other.items())
                else:
                    self.set_items(other.iteritems())
            elif hasattr(other, "keys"):
                self.set_items([
                    (key, other[key])
                    for key in other.keys()
                ])
            else:
                self.set_items([
                    (key, value)
                    for key, value in other
                ])

        if six.PY3:
            self.set_items(kwds.items())
        else:
            self.set_items(kwds.iteritems())

    def __delitem__(self, key):
        key = self.key_encode(key)

        with closing(self.db.cursor()) as c:
            result = c.execute('delete from "%s" where key=?' % self.table, (key, ))
            rows = list(result)

            success = len(rows) > 0

        if not success:
            raise KeyError(key)

    def __getitem__(self, key):
        key = self.key_encode(key)
        row = self.select_one('select value from "%s" where key=?' % self.table, (key, ))

        if not row:
            raise KeyError(key)

        return self.loads(row[0])

    def __iter__(self):
        return self.iterkeys()

    def __len__(self):
        row = self.select_one('select count(*) from "%s"' % self.table)

        if not row:
            return None

        return row[0]

    def __setitem__(self, key, value):
        key = self.key_encode(key)
        value = self.dumps(value)

        with closing(self.db.cursor()) as c:
            c.execute('update "%s" set value=? WHERE key=?' % self.table, (buffer(value), key))
            c.execute('insert or ignore into "%s" values(?,?)' % self.table, (key, buffer(value)))

    def _query_delete(self):
        return 'delete from "%s" where key=?' % self.table

    def _query_upsert(self):
        return 'insert or replace into "%s" values(?,?)' % self.table

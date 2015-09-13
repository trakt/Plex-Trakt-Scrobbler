from stash.archives.core.base import Archive

from contextlib import closing

try:
    import sqlite3
except ImportError:
    sqlite3 = None


class SqliteArchive(Archive):
    __key__  = 'sqlite'

    def __init__(self, db, table):
        super(SqliteArchive, self).__init__()

        if sqlite3 is None:
            raise Exception('Unable to construct sqlite:// - "sqlite3" module is not available')

        self.db = sqlite3.connect(db) if type(db) is str else db
        self.table = table

        # Ensure table exists
        with closing(self.db.cursor()) as c:
            c.execute('create table if not exists "%s" (key PRIMARY KEY, value)' % self.table)

        self.db.commit()

    def iterkeys(self):
        rows = self.select('select key from "%s"' % self.table)

        for row in rows:
            yield self.key_decode(row[0])

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

    def __delitem__(self, key):
        key = self.key_encode(key)

        with closing(self.db.cursor()) as c:
            result = c.execute('delete from "%s" where key=?' % self.table, (key, ))

            success = result.rowcount > 0

        self.db.commit()

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
            c.execute('update "%s" set value=? WHERE key=?' % self.table, (value, key))
            c.execute('insert or ignore into "%s" values(?,?)' % self.table, (key, value))

        self.db.commit()

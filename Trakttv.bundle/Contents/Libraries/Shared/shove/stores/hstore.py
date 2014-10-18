# -*- coding: utf-8 -*-
'''
PostgreSQL hstore store.

shove's URI for PostgreSQL hstore stores follows the form:

hstore://<host>:<port>/<db>/collection/
'''
from shove._compat import urlsplit
from shove.store import BaseStore
from stuf.six import items, values
import logging

try:
    import psycopg2
    from psycopg2 import extras
except ImportError:
    raise ImportError('requires `psycopg2` library')

__all__ = ['HStore']


class HStore(BaseStore):

    '''PostgreSQL hstore object storage frontend.'''

    init = 'mongodb://'

    def __init__(self, engine, **kw):
        super(HStore, self).__init__(engine, **kw)
        spliturl = urlsplit(engine)
        try:
            self._conn = conn = psycopg2.connect(
                host=spliturl.hostname,
                port=spliturl.port,
                database=spliturl.path,
                user=spliturl.username or '',
                password=spliturl.password or '',
            )
            self._store = db = conn.cursor(
                cursor_factory=extras.RealDictCursor
            )
        except psycopg2.OperationalError:
            logging.exception('configuration error')
            raise TypeError('configuration error')
        try:
            db.execute('CREATE EXTENSION hstore')
            conn.commit()
        except psycopg2.ProgrammingError:
            conn.rollback()
        extras.register_hstore(conn)
        try:
            db.execute(
                'CREATE TABLE shove (id serial PRIMARY KEY, data hstore)'
            )
            conn.commit()
            db.execute(
                'INSERT INTO shove (data) VALUES (%s)', ['"key"=>"value"'],
            )
            conn.commit()
            db.execute(
                'UPDATE shove SET data = delete(data, %s)', ['key'],
            )
        except psycopg2.ProgrammingError:
            conn.rollback()

    def __getitem__(self, key):
        try:
            self._store.execute('SELECT data -> %s as t FROM shove', [key])
            data = self._store.fetchone()['t']
            if data is not None:
                return self.loads(data)
            raise KeyError
        except psycopg2.ProgrammingError:
            self._conn.rollback()
            raise KeyError(key)

    def __setitem__(self, key, value):
        try:
            self._store.execute(
                'UPDATE shove SET data = data || (%s)',
                [{key: self.dumps(value)}],
            )
            self._conn.commit()
        except psycopg2.ProgrammingError:
            self._conn.rollback()

    def __delitem__(self, key):
        try:
            self._store.execute(
                'UPDATE shove SET data = delete(data, %s)', [key],
            )
            self._conn.commit()
        except psycopg2.ProgrammingError:
            self._conn.rollback()

    def __contains__(self, key):
        try:
            self._store.execute('SELECT exist(data, %s) FROM shove')
            return self._store.fetchone()['exist']
        except psycopg2.ProgrammingError:
            self._conn.rollback()

    def __len__(self):
        try:
            self._store.execute(
            'SELECT count(k) FROM (SELECT (each(data)).key FROM shove) as k'
            )
            return self._store.fetchone()['count']
        except psycopg2.ProgrammingError:
            self._conn.rollback()

    def __iter__(self):
        try:
            self._store.execute('SELECT akeys(data) as k FROM shove')
            return iter(self._store.fetchall()['k'])
        except psycopg2.ProgrammingError:
            self._conn.rollback()

    def close(self):
        self._conn.close()

    def clear(self):
        pass

    def items(self):
        loads = self.loads
        try:
            self._store.execute('SELECT data as i FROM shove')
            for k, v in items(self._store.fetchall()['i']):
                yield k, loads(v)
        except psycopg2.ProgrammingError:
            self._conn.rollback()

    def values(self):
        loads = self.loads
        try:
            self._store.execute('SELECT svalues(data) as v FROM shove')
            for v in values(self._store.fetchall()['v']):
                yield loads(v)
        except psycopg2.ProgrammingError:
            self._conn.rollback()

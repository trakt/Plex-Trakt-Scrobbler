from __future__ import absolute_import

from exception_wrappers.database.apsw.base import APSWBaseWrapper
from exception_wrappers.database.apsw.raw import APSWConnectionWrapper
from exception_wrappers.libraries.playhouse import apsw_ext
from exception_wrappers.manager import ExceptionSource

from peewee import _sqlite_date_part
from peewee import _sqlite_date_trunc
from peewee import _sqlite_regexp
import sys


class APSWDatabaseWrapper(apsw_ext.APSWDatabase, APSWBaseWrapper):
    def _connect(self, database, **kwargs):
        try:
            conn = APSWConnectionWrapper(database, **kwargs)

            if self.timeout is not None:
                conn.setbusytimeout(self.timeout)

            conn.createscalarfunction('date_part', _sqlite_date_part, 2)
            conn.createscalarfunction('date_trunc', _sqlite_date_trunc, 2)
            conn.createscalarfunction('regexp', _sqlite_regexp, 2)
            self._load_aggregates(conn)
            self._load_collations(conn)
            self._load_functions(conn)
            self._load_modules(conn)
            return conn
        except self.critical_errors:
            self.on_exception(ExceptionSource.APSW, sys.exc_info())

from __future__ import absolute_import

from exception_wrappers.database.apsw.base import APSWBaseWrapper
from exception_wrappers.libraries.playhouse import apsw_ext
from exception_wrappers.manager import ExceptionSource

import sys


class APSWDatabaseWrapper(apsw_ext.APSWDatabase, APSWBaseWrapper):
    def _execute_sql(self, *args, **kwargs):
        try:
            return super(APSWDatabaseWrapper, self)._execute_sql(*args, **kwargs)
        except self.critical_errors:
            self.on_exception(ExceptionSource.APSW, sys.exc_info())

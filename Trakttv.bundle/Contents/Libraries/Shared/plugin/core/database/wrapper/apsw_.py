from plugin.core.database.wrapper.base import APSWBaseWrapper

import apsw
import logging
import sys

log = logging.getLogger(__name__)


class APSWConnectionWrapper(apsw.Connection, APSWBaseWrapper):
    def cursor(self, *args, **kwargs):
        cursor = super(APSWConnectionWrapper, self).cursor(*args, **kwargs)

        # Return wrapped cursor
        return APSWCursorWrapper(self, cursor)


class APSWCursorWrapper(object):
    def __init__(self, connection, cursor):
        self.__connection = connection
        self.__cursor = cursor

    def execute(self, *args, **kwargs):
        try:
            return self.__cursor.execute(*args, **kwargs)
        except self.__connection.critical_errors:
            self.__connection.on_exception(sys.exc_info())

    def __getattr__(self, key):
        if key.startswith('_APSWCursorWrapper__'):
            return getattr(self, key)

        return getattr(self.__cursor, key)

from plugin.core.database.wrapper.base import APSWBaseWrapper

from playhouse import apsw_ext
import logging
import sys

log = logging.getLogger(__name__)


class APSWDatabaseWrapper(apsw_ext.APSWDatabase, APSWBaseWrapper):
    def _execute_sql(self, *args, **kwargs):
        try:
            return super(APSWDatabaseWrapper, self)._execute_sql(*args, **kwargs)
        except self.critical_errors:
            self.on_exception(sys.exc_info())

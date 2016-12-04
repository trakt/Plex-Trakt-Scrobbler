from __future__ import absolute_import

from exception_wrappers.exceptions import DatabaseDisabledError
from exception_wrappers.libraries import apsw
from exception_wrappers.manager import ExceptionWrapper
import logging

log = logging.getLogger(__name__)
disabled_databases = {}


class APSWBaseWrapper(object):
    name = None

    critical_errors = (
        apsw.CantOpenError,
        apsw.CorruptError,
        apsw.FullError,
        apsw.IOError,
        apsw.NotADBError,
        apsw.PermissionsError,
        apsw.ReadOnlyError
    )

    @property
    def error_message(self):
        return disabled_databases.get(self.name)

    @property
    def valid(self):
        return disabled_databases.get(self.name) is None

    def on_exception(self, source, exc_info):
        log.info('Exception raised in %s: %s', source, exc_info[1], exc_info=True)

        # Raise exception if the database is already disabled
        if disabled_databases.get(self.name):
            raise DatabaseDisabledError(exc_info[1])

        # Mark database as disabled
        disabled_databases[self.name] = exc_info

        # Emit exception event
        ExceptionWrapper.add(source, exc_info, self.name)

        # Raise exception
        raise DatabaseDisabledError(exc_info[1])

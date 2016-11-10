from plugin.core.message import InterfaceMessages

import apsw
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

    def on_exception(self, exc_info):
        # Ensure database isn't already disabled
        if disabled_databases.get(self.name):
            # Re-raise exception
            raise exc_info[0], exc_info[1], exc_info[2]

        # Retrieve error message
        message = self.__get_message(exc_info[1])

        # Mark database as disabled
        disabled_databases[self.name] = message

        # Append error message
        InterfaceMessages.add(logging.CRITICAL, message)

        # Display database error
        log.critical(message, exc_info=True)

        # Re-raise exception
        raise exc_info[0], exc_info[1], exc_info[2]

    def __get_message(self, ex):
        name = self.name if self.name else 'unknown'
        name_cap = name.capitalize()

        if type(ex) is apsw.CantOpenError:
            return 'Unable to open %s' % name

        if type(ex) is apsw.CorruptError:
            return '%s is corrupt' % name_cap

        if type(ex) is apsw.FullError:
            return 'Drive containing the %s is full' % name

        if type(ex) is apsw.IOError:
            return '%s raised an input/output error' % name_cap

        if type(ex) is apsw.NotADBError:
            return '%s doesn\'t have a valid SQLite header' % name_cap

        if type(ex) is apsw.PermissionsError:
            return 'Access denied to the %s' % name

        if type(ex) is apsw.ReadOnlyError:
            return 'Unable to write to the %s' % name

        # Unknown exception
        return '%s: %s' % (
            type(ex).__name__,
            ex
        )

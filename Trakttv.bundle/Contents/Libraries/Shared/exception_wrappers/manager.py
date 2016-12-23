from pyemitter import Emitter


class ExceptionSource(object):
    APSW        = 'apsw'
    Peewee      = 'peewee'


class Manager(Emitter):
    def add(self, source, exc_info, name=None):
        if not exc_info or len(exc_info) != 3:
            raise ValueError('Invalid value provided for the "exc_info" parameter')

        # Retrieve error message
        message = self._get_message(exc_info[1], name)

        # Emit event
        self.emit('exception', source, message, exc_info)

    def _get_message(self, exception, name=None):
        if name:
            name_cap = name.capitalize()
        else:
            name = '<unknown>'
            name_cap = '<unknown>'

        # Retrieve exception message
        ex_message = self._clean_exception_message(exception, exception.message)

        # Map exception to a more helpful message
        key = '%s.%s' % (
            type(exception).__module__,
            type(exception).__name__
        )

        if key == 'exceptions.ImportError':
            return 'Unable to import the %s library (%s)' % (name, ex_message)

        if key == 'apsw.CantOpenError':
            return 'Unable to open %s (%s)' % (name, ex_message)

        if key == 'apsw.CorruptError':
            return '%s is corrupt (%s)' % (name_cap, ex_message)

        if key == 'apsw.FullError':
            return 'Drive containing the %s is full (%s)' % (name, ex_message)

        if key == 'apsw.IOError':
            return '%s raised an input/output error (%s)' % (name_cap, ex_message)

        if key == 'apsw.NotADBError':
            return '%s doesn\'t have a valid SQLite header (%s)' % (name_cap, ex_message)

        if key == 'apsw.PermissionsError':
            return 'Access denied to the %s (%s)' % (name, ex_message)

        if key == 'apsw.ReadOnlyError':
            return 'Unable to write to the %s (%s)' % (name, ex_message)

        # Unknown exception
        return '<%s> (%s)' % (key, ex_message)

    @classmethod
    def _clean_exception_message(cls, ex, message):
        if not message:
            return message

        # ImportError
        if isinstance(ex, ImportError) and ':' in message and (message.startswith('/') or message.startswith('./')):
            # Strip path from message (if it looks like a path)
            return message[message.index(':') + 1:].strip().capitalize()

        # Strip exception type prefix from message
        return message.lstrip(type(ex).__name__ + ':').strip()

# Construct default manager
ExceptionWrapper = Manager()

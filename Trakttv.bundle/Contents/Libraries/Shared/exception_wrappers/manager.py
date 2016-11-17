from pyemitter import Emitter


class ExceptionSource(object):
    APSW        = 'apsw'
    Peewee      = 'peewee'


class Manager(Emitter):
    def add(self, source, exc_info, name=None):
        if not exc_info or len(exc_info) != 3:
            raise ValueError('Invalid value provided for the "exc_info" parameter')

        # Retrieve error message
        message = self.__get_message(exc_info[1], name)

        # Emit event
        self.emit('exception', source, message, exc_info)

    def __get_message(self, exception, name=None):
        if name:
            name_cap = name.capitalize()
        else:
            name = '<unknown>'
            name_cap = '<unknown>'

        # Retrieve exception message
        key = '%s.%s' % (
            type(exception).__module__,
            type(exception).__name__
        )

        if key == 'exceptions.ImportError':
            return 'Unable to import the %s library' % name

        if key == 'apsw.CantOpenError':
            return 'Unable to open %s' % name

        if key == 'apsw.CorruptError':
            return '%s is corrupt' % name_cap

        if key == 'apsw.FullError':
            return 'Drive containing the %s is full' % name

        if key == 'apsw.IOError':
            return '%s raised an input/output error' % name_cap

        if key == 'apsw.NotADBError':
            return '%s doesn\'t have a valid SQLite header' % name_cap

        if key == 'apsw.PermissionsError':
            return 'Access denied to the %s' % name

        if key == 'apsw.ReadOnlyError':
            return 'Unable to write to the %s' % name

        # Unknown exception
        return '<%s>' % key

# Construct default manager
ExceptionWrapper = Manager()

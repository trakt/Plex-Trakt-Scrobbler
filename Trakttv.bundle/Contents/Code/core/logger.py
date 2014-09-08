ENTRY_FORMAT = '[%s] %s'


class Logger(object):
    def __init__(self, tag):
        self.tag = tag

    def write(self, func, message, *args, **kwargs):
        tag = self.tag

        if 'tag' in kwargs:
            tag = kwargs.pop('tag')

        try:
            if args:
                message = str(message) % args

            func(ENTRY_FORMAT % (tag, message))
        except Exception, ex:
            Log.Error(
                'Error writing log entry (%s) %s [message: %s, args: %s]',
                type(ex).__name__, ex.message,
                repr(message), args
            )

    def trace(self, message, *args, **kwargs):
        if not Prefs['logging_tracing']:
            return

        self.write(Log.Debug, message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self.write(Log.Debug, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.write(Log.Info, message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        self.write(Log.Warn, message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.write(Log.Error, message, *args, **kwargs)

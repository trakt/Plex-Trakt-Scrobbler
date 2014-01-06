ENTRY_FORMAT = '[%s] %s'


class Logger(object):
    def __init__(self, tag):
        self.tag = tag

    def write(self, func, message, *args):
        func(ENTRY_FORMAT % (self.tag,(message % args)))

    def debug(self, message, *args):
        self.write(Log.Debug, message, *args)

    def info(self, message, *args):
        self.write(Log.Info, message, *args)

    def warn(self, message, *args):
        self.write(Log.Warn, message, *args)

    def error(self, message, *args):
        self.write(Log.Error, message, *args)

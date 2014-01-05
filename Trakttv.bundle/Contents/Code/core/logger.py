ENTRY_FORMAT = '[%s] %s'


class Logger(object):
    def __init__(self, tag):
        self.tag = tag

    def debug(self, message, *args):
        Log.Debug(ENTRY_FORMAT % (self.tag, (message % args)))

    def info(self, message, *args):
        Log.Info(ENTRY_FORMAT % (self.tag, (message % args)))

    def warn(self, message, *args):
        Log.Warn(ENTRY_FORMAT % (self.tag, (message % args)))

    def error(self, message, *args):
        Log.Error(ENTRY_FORMAT % (self.tag, (message % args)))

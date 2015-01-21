import logging
import os

# Setup "TRACE" level
TRACE = 5

logging.addLevelName(TRACE, "TRACE")


class IntLogger(logging.Logger):
    ignore = [
        r'framework.bundle\contents\resources\versions\2\python\framework\code\sandbox.py',
        r'trakttv.bundle\contents\code\core\logger.py'
    ]

    def findCaller(self):
        f = logging.currentframe()

        if f is not None:
            f = f.f_back

        rv = "(unknown file)", 0, "(unknown function)"

        while hasattr(f, "f_code"):
            co = f.f_code
            path = self.normalize_path(co.co_filename)

            if not self.valid(path):
                # Ignore sandbox frame
                f = f.f_back
                continue

            rv = (co.co_filename, f.f_lineno, co.co_name)
            break

        return rv

    @classmethod
    def valid(cls, path):
        for suffix in cls.ignore:
            if path.endswith(suffix):
                return False

        return True

    @staticmethod
    def normalize_path(path):
        return os.path.normcase(path)


# Setup custom logger class
logging.setLoggerClass(IntLogger)


class Logger(object):
    def __init__(self, name=None):

        name = 'plugin%s' % (
            ('.' + name) if name else ''
        )
        self.logger = logging.getLogger(name)

    def trace(self, message, *args, **kwargs):
        self.logger.log(TRACE, message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        self.logger.warn(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

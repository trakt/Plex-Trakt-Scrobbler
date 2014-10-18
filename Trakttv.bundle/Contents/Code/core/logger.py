import logging

# Setup "TRACE" level
TRACE = 5

logging.addLevelName(TRACE, "TRACE")


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

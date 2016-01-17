from plugin.core.constants import PLUGIN_IDENTIFIER
from plugin.core.environment import Environment
from plugin.core.logger.filters import FrameworkFilter, AuthorizationFilter, RequestsFilter
from plugin.core.logger.handlers.error_reporter import ERROR_REPORTER_HANDLER
from plugin.core.logger.handlers.error_storage import ERROR_STORAGE_HANDLER

from logging.handlers import RotatingFileHandler
import logging

LOG_FORMAT = '%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(name)s:%(lineno)d) - %(message)s'
LOG_OPTIONS = {
    'plex':                         'libraries',
    'plex_activity':                'libraries',
    'plex_metadata':                'libraries',
    'raven':                        'libraries',
    'requests':                     'libraries',
    'trakt':                        'libraries',

    'peewee':                       'peewee',
    'peewee_migrate':               'peewee',

    'com.plexapp.plugins.trakttv':  'plugin',
    'plugin':                       'plugin',

    'pyemitter':                    'pyemitter'
}

TRACE = 5

log = logging.getLogger(__name__)


class LogHandler(logging.Handler):
    def __init__(self, handler):
        super(LogHandler, self).__init__()

        self.handler = handler

        # Update formatter for log file
        self.handler.formatter._fmt = LOG_FORMAT

    @property
    def baseFilename(self):
        return self.handler.baseFilename

    def emit(self, record):
        return self.handler.emit(record)


def get_handler():
    logger = logging.getLogger(PLUGIN_IDENTIFIER)

    for h in logger.handlers:
        if type(h) is RotatingFileHandler:
            logger.handlers.remove(h)
            return LogHandler(h)

    return None

def setup():
    # Setup root logger
    rootLogger = logging.getLogger()

    rootLogger.filters = [
        FrameworkFilter()
    ]

    rootLogger.handlers = [
        LOG_HANDLER,
        ERROR_REPORTER_HANDLER,
        ERROR_STORAGE_HANDLER
    ]

    rootLogger.setLevel(logging.DEBUG)

def get_level(option):
    # Try retrieve preference
    try:
        value = Environment.prefs['level_%s' % option]
    except KeyError:
        # Default to "plugin" preference
        value = Environment.prefs['level_plugin']

    # Parse labels into level attributes
    if value == 'ERROR':
        return logging.ERROR

    if value == 'WARN' or value == 'WARNING':
        return logging.WARNING

    if value == 'INFO':
        return logging.INFO

    if value == 'DEBUG':
        return logging.DEBUG

    if value == "TRACE":
        return TRACE

    log.warn('Unknown logging level "%s"', value)
    return logging.DEBUG


def update_loggers():
    for name, option in LOG_OPTIONS.items():
        logger = logging.getLogger(name)

        # Retrieve logger level, check if it has changed
        level = get_level(option)

        if level == logger.level:
            continue

        # Update logger level
        log.debug('Changed %r logger level to %s', name, logging.getLevelName(level))

        logger.setLevel(level)

# Get the logging file handler
LOG_HANDLER = get_handler()
LOG_HANDLER.addFilter(AuthorizationFilter())
LOG_HANDLER.addFilter(RequestsFilter())

# Setup logger
setup()

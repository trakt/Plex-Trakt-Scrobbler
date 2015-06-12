from plugin.core.constants import PLUGIN_IDENTIFIER
from plugin.core.logger.filters.framework import FrameworkFilter
from plugin.core.logger.handlers.error_reporter import ERROR_REPORTER_HANDLER
from plugin.core.logger.handlers.error_storage import ERROR_STORAGE_HANDLER

from logging.handlers import RotatingFileHandler
import logging


def get_handler():
    logger = logging.getLogger(PLUGIN_IDENTIFIER)

    for h in logger.handlers:
        if type(h) is RotatingFileHandler:
            logger.handlers.remove(h)
            return h

    return None

def setup():
    # Update log handler
    setattr(LOG_HANDLER.formatter, '_fmt', '%(asctime)-15s - %(name)-32s (%(thread)x) :  %(levelname)s (%(name)s:%(lineno)d) - %(message)s')

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

# Get the logging file handler
LOG_HANDLER = get_handler()

# Setup logger
setup()

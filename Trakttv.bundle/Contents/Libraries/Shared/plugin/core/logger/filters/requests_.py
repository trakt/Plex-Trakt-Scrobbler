from logging import Filter
from requests import RequestException
import logging


class RequestsFilter(Filter):
    def filter(self, record):
        if self.is_error(record):
            record.levelno = logging.WARN
            record.levelname = 'WARNING'
            return True

        if self.is_dropped_connection(record):
            # Change record level to debug
            record.levelno = logging.DEBUG
            record.levelname = 'DEBUG'

            # Retrieve logger for record
            logger = logging.getLogger(record.name)

            # Check if the logger has debug logging enabled
            return logger.isEnabledFor(logging.DEBUG)

        return True

    @staticmethod
    def is_error(record):
        if record.levelno < logging.ERROR:
            return False

        if not record.exc_info or len(record.exc_info) != 3:
            return False

        exc_type, _, _ = record.exc_info

        if not exc_type or not issubclass(exc_type, RequestException):
            return False

        return True

    @staticmethod
    def is_dropped_connection(record):
        if record.levelno != logging.INFO:
            return False

        if record.name != 'requests.packages.urllib3.connectionpool':
            return False

        if record.msg and not record.msg.startswith('Resetting dropped connection:'):
            return False

        return True

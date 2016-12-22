from logging import Filter
from requests import RequestException
from six import string_types
import logging

IGNORED_MESSAGE_PREFIXES = [
    'Retrying'
]


class RequestsLogFilter(Filter):
    def filter(self, record):
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
    def is_dropped_connection(record):
        if record.levelno != logging.INFO:
            return False

        if record.name != 'requests.packages.urllib3.connectionpool':
            return False

        if record.msg and not record.msg.startswith('Resetting dropped connection:'):
            return False

        return True


class RequestsReportFilter(Filter):
    def filter(self, record):
        if self.is_requests_exception(record):
            return False

        if self.is_ignored_message(record):
            return False

        return True

    @staticmethod
    def is_ignored_message(record):
        if record.levelno < logging.WARNING:
            return False

        for prefix in IGNORED_MESSAGE_PREFIXES:
            if isinstance(record.msg, string_types) and record.msg.startswith(prefix):
                return True

        return False

    @staticmethod
    def is_requests_exception(record):
        if record.levelno < logging.WARNING:
            return False

        if not record.exc_info or len(record.exc_info) != 3:
            return False

        exc_type, _, _ = record.exc_info

        if not exc_type or not issubclass(exc_type, RequestException):
            return False

        return True

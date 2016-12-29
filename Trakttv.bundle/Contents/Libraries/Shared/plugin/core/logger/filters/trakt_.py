from logging import Filter
from six import string_types
from trakt.core.exceptions import ServerError, RequestError
import logging

IGNORED_MESSAGE_PREFIXES = [
    'Continue retry since status is',
    'OAuth - Unable to refresh expired token',
    'request failed:',
    'Retry #'
]


class TraktReportFilter(Filter):
    def filter(self, record):
        if self.is_server_error(record):
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
    def is_server_error(record):
        if record.levelno < logging.WARNING:
            return False

        if not record.exc_info or len(record.exc_info) != 3:
            return False

        exc_type, _, _ = record.exc_info

        if not exc_type or not issubclass(exc_type, ServerError):
            return False

        return True


class TraktNetworkFilter(Filter):
    def __init__(self, mode='exclude'):
        super(TraktNetworkFilter, self).__init__()

        if mode not in ['exclude', 'include']:
            raise ValueError('Unknown filter mode: %r' % mode)

        self.mode = mode

    def filter(self, record):
        if self.mode == 'exclude':
            return (
                not self.is_trakt_request_failed(record) and
                not self.is_trakt_request_exception(record)
            )

        if self.mode == 'include':
            return (
                self.is_trakt_request_failed(record) or
                self.is_trakt_request_exception(record)
            )

        return True

    @staticmethod
    def is_trakt_request_exception(record):
        if record.levelno < logging.WARNING:
            return False

        if not record.exc_info or len(record.exc_info) != 3:
            return False

        exc_type, _, _ = record.exc_info

        if not exc_type or not issubclass(exc_type, RequestError):
            return False

        return True

    @staticmethod
    def is_trakt_request_failed(record):
        if record.levelno < logging.WARNING:
            return False

        if record.name != 'trakt.interfaces.base':
            return False

        if not record.msg:
            return False

        return record.msg.startswith('Request failed:')

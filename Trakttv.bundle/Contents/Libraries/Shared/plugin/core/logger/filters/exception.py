from plugin.core.exceptions import AccountAuthenticationError

from logging import Filter
import logging

IGNORED_EXCEPTIONS = [
    AccountAuthenticationError
]

IGNORED_NAMES = [
    'NotADBError'
]


class ExceptionReportFilter(Filter):
    def filter(self, record):
        if self.is_ignored_exception(record):
            return False

        return True

    @staticmethod
    def is_ignored_exception(record):
        if record.levelno < logging.WARNING:
            return False

        if not record.exc_info or len(record.exc_info) != 3:
            return False

        exc_type, _, _ = record.exc_info

        if not exc_type:
            return False

        return (
            exc_type in IGNORED_EXCEPTIONS
        ) or (
            exc_type.__name__ in IGNORED_NAMES
        )

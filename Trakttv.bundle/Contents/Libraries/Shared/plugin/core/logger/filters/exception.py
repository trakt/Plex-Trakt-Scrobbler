from plugin.core.exceptions import AccountAuthenticationError, PluginDisabledError

from exception_wrappers import DisabledError
from logging import Filter
import logging
import re

EXCEPTION_REGEX = re.compile(
    r"^Exception.*\(most recent call last\):.*\n(?P<exc_name>\w+): (.*)(?:\n|$)",
    re.DOTALL | re.IGNORECASE
)

IGNORED_EXCEPTIONS = [
    AccountAuthenticationError,
    DisabledError
]

IGNORED_NAMES = [
    ex.__name__ for ex in IGNORED_EXCEPTIONS
] + [
    'NotADBError'
]


class ExceptionReportFilter(Filter):
    def filter(self, record):
        if self.is_ignored_exception(record):
            return False

        return True

    @classmethod
    def is_ignored_exception(cls, record):
        if record.levelno < logging.WARNING:
            return False

        # Retrieve exception details
        exc_name = None
        exc_type = None

        if record.exc_info and len(record.exc_info) == 3:
            exc_type, _, _ = record.exc_info
            exc_name = exc_type.__name__
        else:
            match = EXCEPTION_REGEX.match(record.message)

            if not match:
                return False

            exc_name = match.group('exc_name')

        if exc_type and cls.is_ignored_exception_type(exc_type):
            return True

        if exc_name and exc_name in IGNORED_NAMES:
            return True

        return False

    @classmethod
    def is_ignored_exception_type(cls, exc_type):
        if not exc_type:
            return False

        for item in IGNORED_EXCEPTIONS:
            if exc_type is item or issubclass(exc_type, item):
                return True

        return False

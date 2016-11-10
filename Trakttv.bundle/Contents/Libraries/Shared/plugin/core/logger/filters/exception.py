from plugin.core.exceptions import AccountAuthenticationError, PluginDisabledError

from logging import Filter
import logging
import re

EXCEPTION_REGEX = re.compile(
    r"^Exception.*\(most recent call last\):.*\n(?P<exc_name>\w+): (.*)(?:\n|$)",
    re.DOTALL | re.IGNORECASE
)

IGNORED_EXCEPTIONS = [
    AccountAuthenticationError,
    PluginDisabledError
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

    @staticmethod
    def is_ignored_exception(record):
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

        if exc_type and exc_type in IGNORED_EXCEPTIONS:
            return True

        if exc_name and exc_name in IGNORED_NAMES:
            return True

        return False

from logging import Filter
from trakt.core.exceptions import ServerError
import logging


class TraktReportFilter(Filter):
    def filter(self, record):
        if self.is_server_error(record):
            return False

        return True

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

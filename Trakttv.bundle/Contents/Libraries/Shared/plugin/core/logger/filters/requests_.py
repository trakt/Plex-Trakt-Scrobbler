from logging import Filter
from requests import RequestException
import logging


class RequestsFilter(Filter):
    def filter(self, record):
        if self.is_request_error(record):
            return False

        return True

    @staticmethod
    def is_request_error(record):
        if record.levelno < logging.ERROR:
            return False

        if not record.exc_info or len(record.exc_info) != 3:
            return False

        exc_type, _, _ = record.exc_info

        if not exc_type or not issubclass(exc_type, RequestException):
            return False

        return True

from logging import Filter
import logging


class FrameworkFilter(Filter):
    def filter(self, record):
        if self.is_ioloop_error(record):
            return False

        return True

    @staticmethod
    def is_ioloop_error(record):
        if record.levelno < logging.ERROR:
            return False

        if record.name != 'root':
            return False

        if record.filename != 'ioloop.py':
            return False

        return True

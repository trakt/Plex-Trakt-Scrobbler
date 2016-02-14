from logging import Filter
import logging


class FrameworkFilter(Filter):
    def filter(self, record):
        level = self.map(record)

        if level is None:
            return True

        record.levelno = level
        record.levelname = logging.getLevelName(level)
        return True

    @staticmethod
    def map(record):
        if record.levelno < logging.ERROR:
            return None

        if record.name != 'root':
            return None

        if not record.pathname:
            return None

        path = record.pathname.lower().replace('\\', '/')

        if path.endswith('/libraries/tornado/ioloop.py'):
            return logging.INFO

        if path.endswith('/framework/components/runtime.py'):
            return logging.INFO

        if path.endswith('/framework/core.py'):
            return logging.INFO

        return None

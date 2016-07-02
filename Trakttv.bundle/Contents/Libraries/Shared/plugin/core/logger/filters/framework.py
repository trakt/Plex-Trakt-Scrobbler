from logging import Filter
import logging

FRAMEWORK_FILES = [
    '/framework/components/runtime.py',
    '/framework/core.py',
    '/libraries/tornado/ioloop.py',
    '/libraries/tornado/iostream.py'
]


class FrameworkFilter(Filter):
    def filter(self, record):
        level = self.map(record)

        if level is None:
            return True

        record.levelno = level
        record.levelname = logging.getLevelName(level)
        return True

    @classmethod
    def map(cls, record):
        if record.levelno < logging.ERROR:
            return None

        if record.name != 'root':
            return None

        if not record.pathname:
            return None

        path = record.pathname.lower().replace('\\', '/')

        if cls.is_framework_file(path):
            return logging.DEBUG

        return None

    @staticmethod
    def is_framework_file(path):
        for name in FRAMEWORK_FILES:
            if path.endswith(name):
                return True

        return None

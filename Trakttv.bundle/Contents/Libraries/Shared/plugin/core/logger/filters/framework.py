from logging import Filter
import logging
import re

TRACEBACK_REGEX = re.compile(
    r"(?:\n|^)Exception(?: (?P<message>.*))? \(most recent call last\):\n"
    r"(?P<stacktrace>.*?)\n(?P<ex_type>\w+): (?P<ex_message>.*?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL
)

FRAME_REGEX = re.compile(
    r"(?:\n|^)?\s*File \"(?P<path>.*?)\", line (?P<line_num>\d+), "
    r"in (?P<function>\w+)\n\s*(?P<line>.*?)(?:\n|$)",
    re.IGNORECASE | re.DOTALL
)

FRAMEWORK_FILES = [
    '/framework/components/runtime.py',
    '/framework/core.py',
    '/libraries/tornado/ioloop.py',
    '/libraries/tornado/iostream.py'
]


class FrameworkFilter(Filter):
    def __init__(self, mode='map'):
        super(FrameworkFilter, self).__init__()

        self.mode = mode

    def filter(self, record):
        if not hasattr(record, 'message'):
            record.message = record.getMessage()

        # Ensure record is from the plugin framework
        if not self.is_framework_record(record):
            return True

        # Map (or filter) record
        if self.mode == 'map':
            record.levelno = logging.DEBUG
            record.levelname = logging.getLevelName(logging.DEBUG)
        elif self.mode == 'filter':
            return False

        return True

    @classmethod
    def is_framework_record(cls, record):
        if record.levelno < logging.ERROR:
            return False

        if record.name not in ['root', 'com.plexapp.plugins.trakttv']:
            return False

        if not record.pathname:
            return False

        # Ensure record was emitted by a framework module
        if not cls.is_framework_file(record.pathname):
            return False

        # Ensure exception was raised by the plugin framework
        if not cls.is_framework_exception(record):
            return False

        return True

    @classmethod
    def is_framework_file(cls, path):
        path = path.lower().replace('\\', '/')

        for name in FRAMEWORK_FILES:
            if path.endswith(name):
                return True
        return False

    @classmethod
    def is_framework_exception(cls, record):
        if record.exc_info and len(record.exc_info) == 3:
            # Retrieve traceback from record exception information
            traceback = record.exc_info[2]

            if not traceback.tb_frame:
                return False

            # Retrieve final frame path
            frame = traceback.tb_frame

            if not frame.f_code or not frame.f_code.co_filename:
                return False

            path = frame.f_code.co_filename

            # Ensure exception was raised by the plugin framework
            return cls.is_framework_file(path)

        # Parse traceback from record message
        traceback = cls.parse_traceback(record.message)

        if not traceback['frames']:
            return False

        # Retrieve final frame path
        frame = traceback['frames'][-1]

        if not frame.get('path'):
            return False

        path = frame['path']

        # Ensure exception was raised by the plugin framework
        return cls.is_framework_file(path)

    @classmethod
    def parse_traceback(cls, message):
        # Match traceback
        traceback = TRACEBACK_REGEX.match(message)

        if not traceback:
            return None

        # Build result
        result = traceback.groupdict()
        result['frames'] = cls.parse_frames(result.get('stacktrace', ''))

        return result

    @classmethod
    def parse_frames(cls, stacktrace):
        result = []

        for frame in FRAME_REGEX.finditer(stacktrace):
            result.append(frame.groupdict())

        return result

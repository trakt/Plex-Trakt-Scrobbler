from six import add_metaclass
from sortedcontainers import SortedSet
import collections
import logging
import sys
import time

Record = collections.namedtuple('Record', 'level timestamp message')
log = logging.getLogger(__name__)


class InterfaceMessagesMeta(type):
    @property
    def critical(cls):
        return cls.severity >= logging.CRITICAL

    @property
    def message(cls):
        if not cls.records:
            return logging.NOTSET

        # Return the latest highest level/severity message
        return cls.records[-1].message

    @property
    def record(cls):
        if not cls.records:
            return None

        return cls.records[-1]

    @property
    def severity(cls):
        if not cls.records:
            return logging.NOTSET

        # Return the highest error level/severity
        return cls.records[-1].level


@add_metaclass(InterfaceMessagesMeta)
class InterfaceMessages(object):
    records = SortedSet()

    @classmethod
    def add(cls, level, message, *args):
        cls.records.add(Record(
            level=level,
            timestamp=time.time(),
            message=message % args
        ))

    @classmethod
    def add_exception(cls, level, message, exc_info=None):
        if exc_info is None:
            exc_info = sys.exc_info()

        # Parse exception information
        if len(exc_info) == 3:
            _, ex, tb = exc_info
        else:
            _, ex, tb = (None, None, None)

        # Retrieve exception message
        ex_message = None

        if ex and hasattr(ex, 'message') and ex.message:
            ex_message = ex.message
        elif ex:
            ex_message = type(ex).__name__

        # Clean exception message
        ex_message = cls._clean_exception_message(ex, ex_message)

        # Format message
        if ex_message:
            # Format message with exception
            try:
                message = '%s: %r' % (message, ex_message)
            except Exception as ex:
                log.warn('Unable to format message: %s', ex)
                message = ex_message

        if not message:
            log.warn('Ignoring add_exception() call, no message was provided')
            return

        # Append message to log file
        log.log(level, message, exc_info=exc_info)

        # Add interface message record
        cls.records.add(Record(
            level=level,
            timestamp=time.time(),
            message=message
        ))

    @classmethod
    def _clean_exception_message(cls, ex, message):
        if not message:
            return message

        # ImportError
        if isinstance(ex, ImportError):
            if ':' not in message:
                return message

            if not message.startswith('/') or not message.startswith('./'):
                return message

            # Strip path from message
            return message[message.index(':') + 1:].strip().capitalize()

        # Unknown exception type
        return message

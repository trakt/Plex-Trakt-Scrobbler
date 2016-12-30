from exception_wrappers import ExceptionWrapper
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
        try:
            message = message % args
        except TypeError:
            log.warn('Unable to format string %r, with arguments: %r', message, args)

        # Append message to log file
        if level <= logging.CRITICAL:
            log.log(level, message)
        else:
            log.log(logging.CRITICAL, message)

        # Add interface message record
        cls.records.add(Record(
            level=level,
            timestamp=time.time(),
            message=message
        ))

    @classmethod
    def add_exception(cls, level, message, exc_info=None):
        if exc_info is None:
            exc_info = sys.exc_info()

        # Ensure message has been provided
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
    def bind(cls):
        ExceptionWrapper.on('exception', cls._on_exception)

        log.info('Bound to exception events')

    @classmethod
    def _on_exception(cls, source, message, exc_info):
        # Append error message
        InterfaceMessages.add_exception(logging.CRITICAL, message, exc_info)

from six import add_metaclass
from sortedcontainers import SortedSet
import collections
import logging
import time

Record = collections.namedtuple('Record', 'level timestamp message')


class MessageManagerMeta(type):
    @property
    def blocked(cls):
        return cls.severity >= logging.CRITICAL

    @property
    def message(cls):
        if not cls.errors:
            return logging.NOTSET

        # Return the latest highest level/severity message
        return cls.errors[-1].message

    @property
    def record(cls):
        if not cls.errors:
            return None

        return cls.errors[-1]

    @property
    def severity(cls):
        if not cls.errors:
            return logging.NOTSET

        # Return the highest error level/severity
        return cls.errors[-1].level


@add_metaclass(MessageManagerMeta)
class MessageManager(object):
    errors = SortedSet()

    @classmethod
    def add(cls, level, message, *args):
        cls.errors.add(Record(
            level=level,
            timestamp=time.time(),
            message=message % args
        ))

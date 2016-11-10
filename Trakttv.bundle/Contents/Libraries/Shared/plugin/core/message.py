from six import add_metaclass
from sortedcontainers import SortedSet
import collections
import logging
import time

Record = collections.namedtuple('Record', 'level timestamp message')


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

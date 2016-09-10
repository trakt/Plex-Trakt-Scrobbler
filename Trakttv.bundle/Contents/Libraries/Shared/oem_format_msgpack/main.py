from oem_framework.format import Format
from oem_framework.plugin import Plugin

import logging

try:
    import msgpack
except ImportError:
    msgpack = None

log = logging.getLogger(__name__)


class MessagePackFormat(Format, Plugin):
    __key__ = 'msgpack'

    __extension__ = 'mpack'
    __supports_binary__ = True

    @property
    def available(self):
        return msgpack is not None

    def dump_file(self, obj, fp):
        try:
            msgpack.dump(obj, fp)
            return True
        except Exception as ex:
            log.warn('Unable to dump object to file: %s', ex, exc_info=True)

        return False

    def dump_string(self, obj):
        try:
            msgpack.dumps(obj)
            return True
        except Exception as ex:
            log.warn('Unable to dump object: %s', ex, exc_info=True)

        return False

    def load_file(self, fp):
        try:
            return msgpack.load(fp)
        except Exception as ex:
            log.warn('Unable to load object from file: %s', ex, exc_info=True)

        return None

    def load_string(self, value):
        try:
            return msgpack.loads(value)
        except Exception as ex:
            log.warn('Unable to load object: %s', ex, exc_info=True)

        return None

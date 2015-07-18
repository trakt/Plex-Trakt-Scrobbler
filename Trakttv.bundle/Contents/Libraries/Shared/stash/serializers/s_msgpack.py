from stash.serializers.core.base import Serializer

import stash.lib.six as six

try:
    import msgpack
except ImportError:
    msgpack = None


class MessagePackSerializer(Serializer):
    __key__ = 'msgpack'

    def dumps(self, value):
        if msgpack is None:
            raise Exception('"msgpack" library is not available')

        # Dump object
        value = msgpack.dumps(value)

        value = six.text_type(value, 'raw_unicode_escape')

        # Return UTF-8 string
        return value.encode('utf-8')

    def loads(self, value):
        if msgpack is None:
            raise Exception('"msgpack" library is not available')

        # Convert `buffer` -> UTF-8 string
        value = str(value).decode('utf-8')

        value = value.encode('raw_unicode_escape')

        # Return decoded object
        return msgpack.loads(value)

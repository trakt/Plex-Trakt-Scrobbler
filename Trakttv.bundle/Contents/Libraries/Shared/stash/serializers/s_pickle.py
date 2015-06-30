from stash.core.helpers import to_integer
from stash.serializers.core.base import Serializer

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class PickleSerializer(Serializer):
    __key__ = 'pickle'

    def __init__(self, protocol=0):
        super(PickleSerializer, self).__init__()

        self.protocol = to_integer(protocol)

    def dumps(self, value):
        # Dump object
        value = pickle.dumps(value, protocol=self.protocol)

        # Build unicode string from `value`
        value = unicode(value, 'raw_unicode_escape')

        # Return UTF-8 string
        return value.encode('utf-8')

    def loads(self, value):
        # Convert `buffer` -> UTF-8 string
        value = str(value).decode('utf-8')

        # Build `StringIO` object from raw unicode string
        value = StringIO(value.encode('raw_unicode_escape'))

        # Return decoded object
        return pickle.load(value)

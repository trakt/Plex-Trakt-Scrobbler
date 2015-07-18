from stash.core.helpers import to_integer
from stash.serializers.core.base import Serializer

import stash.lib.six as six

try:
    import cPickle as pickle
except ImportError:
    import pickle

from stash.lib.six import BytesIO


class PickleSerializer(Serializer):
    __key__ = 'pickle'

    def __init__(self, protocol=0):
        super(PickleSerializer, self).__init__()

        self.protocol = to_integer(protocol)

    def dumps(self, value):
        # Dump object
        value = pickle.dumps(value, protocol=self.protocol)

        # Build unicode string from `value`
        value = six.text_type(value, 'latin-1')

        # Return UTF-8 string
        return value.encode('utf-8')

    def loads(self, value):
        # Convert `buffer` -> UTF-8 string
        if six.PY3:
            value = value.decode('utf-8')
        else:
            value = str(value).decode('utf-8')

        # Build `BytesIO` object from raw unicode string
        value = BytesIO(value.encode('latin-1'))

        # Return decoded object
        return pickle.load(value)

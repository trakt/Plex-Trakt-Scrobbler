from stash.serializers.core.base import Serializer

try:
    import jsonpickle
except ImportError:
    jsonpickle = None


class JsonPickleSerializer(Serializer):
    __key__ = 'jsonpickle'

    def dumps(self, value):
        if jsonpickle is None:
            raise Exception('"jsonpickle" library is not available')

        return jsonpickle.encode(value)

    def loads(self, value):
        if jsonpickle is None:
            raise Exception('"jsonpickle" library is not available')

        return jsonpickle.decode(value)

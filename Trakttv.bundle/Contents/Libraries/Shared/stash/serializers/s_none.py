from stash.serializers.core.base import Serializer


class NoneSerializer(Serializer):
    __key__ = 'none'

    def dumps(self, value):
        return value

    def loads(self, value):
        return value

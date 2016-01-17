from stash.core.modules.base import Module


class Serializer(Module):
    __group__ = 'serializer'

    def dumps(self, value):
        raise NotImplementedError

    def loads(self, value):
        raise NotImplementedError

from plugin.api.core.base import Service


class System(Service):
    __key__ = 'system'

    @classmethod
    def test(cls, *args, **kwargs):
        return {
            'args': args,
            'kwargs': kwargs
        }

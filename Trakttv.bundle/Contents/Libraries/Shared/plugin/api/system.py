from plugin.api.core.base import Service


class System(Service):
    @classmethod
    def test(cls, *args, **kwargs):
        return 'not implemented'

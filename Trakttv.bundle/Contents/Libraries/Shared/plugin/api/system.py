from plugin.api.core.base import Service
from plugin.core.constants import PLUGIN_VERSION


class System(Service):
    __key__ = 'system'

    @classmethod
    def test(cls, *args, **kwargs):
        return {
            'args': args,
            'kwargs': kwargs
        }

    @classmethod
    def ping(cls):
        return {
            'version': PLUGIN_VERSION
        }

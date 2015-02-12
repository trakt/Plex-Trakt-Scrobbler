from plugin.core.method_manager import MethodManager
from plugin.scrobbler.methods import Logging, WebSocket


class Scrobbler(object):
    methods = MethodManager([
        WebSocket,
        Logging
    ])
    started = []


    @classmethod
    def start(cls, blocking=False):
        cls.started = cls.methods.start()

from plugin.core.helpers.thread import module
from plugin.core.method_manager import MethodManager
from plugin.scrobbler.methods import Logging, WebSocket


@module(start=True, blocking=True)
class Scrobbler(object):
    methods = MethodManager([
        WebSocket,
        Logging
    ])
    started = []


    @classmethod
    def start(cls, blocking=False):
        cls.started = cls.methods.start()

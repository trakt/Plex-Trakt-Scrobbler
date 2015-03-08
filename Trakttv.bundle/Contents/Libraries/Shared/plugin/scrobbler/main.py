from plugin.core.constants import ACTIVITY_MODE
from plugin.core.environment import Environment
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
        enabled = ACTIVITY_MODE.get(Environment.prefs['activity_mode'])

        # Start methods
        cls.started = cls.methods.start(enabled)

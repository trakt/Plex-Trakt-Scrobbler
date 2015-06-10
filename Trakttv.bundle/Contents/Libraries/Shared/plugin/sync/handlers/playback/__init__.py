from plugin.sync import SyncData
from plugin.sync.handlers.core.base.mode import ModeHandler
from plugin.sync.handlers.playback.pull import Pull
from plugin.sync.handlers.playback.push import Push


class Playback(ModeHandler):
    data = SyncData.Playback
    children = [
        Pull,
        Push
    ]

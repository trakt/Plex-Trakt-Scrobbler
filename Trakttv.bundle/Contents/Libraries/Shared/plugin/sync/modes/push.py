from plugin.sync.core.enums import SyncMode
from plugin.sync.modes.core.base import Mode


class Push(Mode):
    mode = SyncMode.Push

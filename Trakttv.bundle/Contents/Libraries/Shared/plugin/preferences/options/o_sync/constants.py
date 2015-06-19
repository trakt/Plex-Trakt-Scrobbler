from plugin.sync.core.enums import SyncMode
from plugin.sync.core.task.configuration.options import ConflictResolution

PLEX_CONFLICT_RESOLUTION = {
    'latest':                       ConflictResolution.Latest,
    'trakt':                        ConflictResolution.Trakt,
    'plex':                         ConflictResolution.Plex
}

PLEX_MODES = {
    'Disabled':                     None,
    'Synchronize (Pull + Push)':    SyncMode.Full,
    'Pull':                         SyncMode.Pull,
    'Push':                         SyncMode.Push
}

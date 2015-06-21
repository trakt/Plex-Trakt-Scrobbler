from plugin.core.enums import ConflictResolution
from plugin.sync.core.enums import SyncMode

#
# Conflict resolution
#

CONFLICT_RESOLUTION_BY_KEY = {
    ConflictResolution.Latest:  'Latest',
    ConflictResolution.Trakt:   'Trakt',
    ConflictResolution.Plex:    'Plex'
}

CONFLICT_RESOLUTION_BY_LABEL = {
    'latest':                       ConflictResolution.Latest,
    'trakt':                        ConflictResolution.Trakt,
    'plex':                         ConflictResolution.Plex
}

#
# Sync modes
#

MODES_BY_KEY = {
    None:               'Disabled',
    SyncMode.FastPull:  'Fast Pull',
    SyncMode.Full:      'Full (Fast Pull + Push)',
    SyncMode.Pull:      'Pull',
    SyncMode.Push:      'Push'
}

MODES_BY_LABEL = {
    'Disabled':                     None,
    'Synchronize (Pull + Push)':    SyncMode.Full,
    'Pull':                         SyncMode.Pull,
    'Push':                         SyncMode.Push
}

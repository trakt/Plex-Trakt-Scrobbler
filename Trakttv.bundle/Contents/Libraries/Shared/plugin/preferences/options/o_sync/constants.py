from plugin.core.enums import ConflictResolution
from plugin.sync.core.enums import SyncMode

#
# Conflict resolution
#

RESOLUTION_IDS_BY_KEY = {
    ConflictResolution.Latest:  0,
    ConflictResolution.Trakt:   1,
    ConflictResolution.Plex:    2
}

RESOLUTION_KEYS_BY_LABEL = {
    'latest':                       ConflictResolution.Latest,
    'trakt':                        ConflictResolution.Trakt,
    'plex':                         ConflictResolution.Plex
}

RESOLUTION_LABELS_BY_KEY = {
    ConflictResolution.Latest:  'Latest',
    ConflictResolution.Trakt:   'Trakt',
    ConflictResolution.Plex:    'Plex'
}

#
# Sync modes
#

MODE_IDS_BY_KEY = {
    None:               0,
    SyncMode.Full:      1,
    SyncMode.Pull:      2,
    SyncMode.Push:      3,
    SyncMode.FastPull:  4
}

MODE_KEYS_BY_LABEL = {
    'Disabled':                     None,
    'Synchronize (Pull + Push)':    SyncMode.Full,
    'Pull':                         SyncMode.Pull,
    'Push':                         SyncMode.Push
}

MODE_LABELS_BY_KEY = {
    None:               'Disabled',
    SyncMode.FastPull:  'Fast Pull',
    SyncMode.Full:      'Full (Fast Pull + Push)',
    SyncMode.Pull:      'Pull',
    SyncMode.Push:      'Push'
}

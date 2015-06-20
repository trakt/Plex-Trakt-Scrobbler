from plugin.sync.core.enums import SyncMode

#
# Conflict resolution
#

class ConflictResolution(object):
    Latest  = 0x00
    Trakt   = 0x01
    Plex    = 0x02


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

from plugin.sync.core.enums import SyncConflictResolution, SyncMode, SyncActionMode

#
# Artifact modes
#

ACTION_MODE_LABELS_BY_KEY = {
    None:                   'Default',
    SyncActionMode.Update:  'Update',
    SyncActionMode.Log:     'Log'
}

#
# Conflict resolution
#

RESOLUTION_IDS_BY_KEY = {
    SyncConflictResolution.Latest:  0,
    SyncConflictResolution.Trakt:   1,
    SyncConflictResolution.Plex:    2
}

RESOLUTION_KEYS_BY_LABEL = {
    'latest':                       SyncConflictResolution.Latest,
    'trakt':                        SyncConflictResolution.Trakt,
    'plex':                         SyncConflictResolution.Plex
}

RESOLUTION_LABELS_BY_KEY = {
    SyncConflictResolution.Latest:  'Latest',
    SyncConflictResolution.Trakt:   'Trakt',
    SyncConflictResolution.Plex:    'Plex'
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

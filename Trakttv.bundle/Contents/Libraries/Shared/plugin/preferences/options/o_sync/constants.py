from plugin.sync.core.enums import SyncConflictResolution, SyncMode, SyncActionMode, SyncInterval

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
# Interval
#

INTERVAL_IDS_BY_KEY = {
    None:               0,

    SyncInterval.M15:   1,
    SyncInterval.M30:   2,

    SyncInterval.H1:    3,
    SyncInterval.H3:    4,
    SyncInterval.H6:    5,
    SyncInterval.H12:   6,

    SyncInterval.D1:    7,
    SyncInterval.D7:    8
}

INTERVAL_KEYS_BY_LABEL = {
    'Disabled':         None,

    '15 Minutes':       SyncInterval.M15,
    '30 Minutes':       SyncInterval.M30,

    'Hour':             SyncInterval.H1,
    '3 Hours':          SyncInterval.H3,
    '6 Hours':          SyncInterval.H6,
    '12 Hours':         SyncInterval.H12,

    'Day':              SyncInterval.D1,
    'Week':             SyncInterval.D7
}

INTERVAL_LABELS_BY_KEY = {
    None:               'Disabled',

    SyncInterval.M15:   '15 Minutes',
    SyncInterval.M30:   '30 Minutes',

    SyncInterval.H1:    'Hour',
    SyncInterval.H3:    '3 Hours',
    SyncInterval.H6:    '6 Hours',
    SyncInterval.H12:   '12 Hours',

    SyncInterval.D1:    'Day',
    SyncInterval.D7:    'Week'
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

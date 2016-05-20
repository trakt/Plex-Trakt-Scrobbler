from plugin.sync.core.enums import SyncConflictResolution, SyncMode, SyncActionMode, SyncInterval, SyncProfilerMode, \
    SyncIdleDelay, ScrobbleDuplicationPeriod

#
# Artifact modes
#

ACTION_MODE_LABELS_BY_KEY = {
    None:                   'Default',
    SyncActionMode.Update:  'Update',
    SyncActionMode.Log:     'Log'
}

#
# Profiler modes
#

PROFILER_MODE_LABELS_BY_KEY = {
    SyncProfilerMode.Disabled:  'Disabled',
    SyncProfilerMode.Basic:     'Basic'
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
# Duplication period
#

DUPLICATION_PERIOD_IDS_BY_KEY = {
    None:                            0,

    ScrobbleDuplicationPeriod.H1:    1,
    ScrobbleDuplicationPeriod.H3:    2,
    ScrobbleDuplicationPeriod.H6:    3,
    ScrobbleDuplicationPeriod.H12:   4,

    ScrobbleDuplicationPeriod.D1:    5,
    ScrobbleDuplicationPeriod.D7:    6
}

DUPLICATION_PERIOD_KEYS_BY_LABEL = {
    'Disabled':         None,

    '1 Hour':           ScrobbleDuplicationPeriod.H1,
    '3 Hours':          ScrobbleDuplicationPeriod.H3,
    '6 Hours':          ScrobbleDuplicationPeriod.H6,
    '12 Hours':         ScrobbleDuplicationPeriod.H12,

    '1 Day':            ScrobbleDuplicationPeriod.D1,
    '7 Days':           ScrobbleDuplicationPeriod.D7
}

DUPLICATION_PERIOD_LABELS_BY_KEY = {
    None:                            'Disabled',

    ScrobbleDuplicationPeriod.H1:    '1 Hour',
    ScrobbleDuplicationPeriod.H3:    '3 Hours',
    ScrobbleDuplicationPeriod.H6:    '6 Hours',
    ScrobbleDuplicationPeriod.H12:   '12 Hours',

    ScrobbleDuplicationPeriod.D1:    '1 Day',
    ScrobbleDuplicationPeriod.D7:    '7 Days'
}

#
# Idle delay
#

IDLE_DELAY_IDS_BY_KEY = {
    SyncIdleDelay.M15:   0,
    SyncIdleDelay.M30:   1,
    SyncIdleDelay.H1:    2,
}

IDLE_DELAY_KEYS_BY_LABEL = {
    '15 Minutes':       SyncIdleDelay.M15,
    '30 Minutes':       SyncIdleDelay.M30,
    'Hour':             SyncIdleDelay.H1
}

IDLE_DELAY_LABELS_BY_KEY = {
    SyncIdleDelay.M15:   '15 Minutes',
    SyncIdleDelay.M30:   '30 Minutes',
    SyncIdleDelay.H1:    'Hour'
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

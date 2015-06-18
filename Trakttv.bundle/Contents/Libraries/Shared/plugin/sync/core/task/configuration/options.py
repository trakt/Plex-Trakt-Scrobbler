from plugin.sync.core.task.configuration.property import Property
from plugin.sync.core.enums import SyncMode

# Sync collection modes
MODES = {
    None:               'Disabled',
    SyncMode.FastPull:  'Fast Pull',
    SyncMode.Full:      'Full (Fast Pull + Push)',
    SyncMode.Pull:      'Pull',
    SyncMode.Push:      'Push'
}

# Conflict Resolution
class ConflictResolution(object):
    Latest  = 0x00
    Trakt   = 0x01
    Plex    = 0x02

CONFLICT_RESOLUTION = {
    ConflictResolution.Latest:  'Latest',
    ConflictResolution.Trakt:   'Trakt',
    ConflictResolution.Plex:    'Plex'
}

OPTIONS = [
    #
    # Collection
    #

    Property(
        'collection.mode',
        group=('Sync', 'Collection'),
        label='Mode',

        type='enum',
        default=None,
        options=MODES
    ),

    Property(
        'collection.clean',
        group=('Sync', 'Collection'),
        label='Clean collection',

        type='boolean',
        default=False
    ),

    #
    # Playback
    #

    Property(
        'playback.mode',
        group=('Sync', 'Playback'),
        label='Mode',

        type='enum',
        default=None,
        options=MODES
    ),

    #
    # Ratings
    #

    Property(
        'ratings.mode',
        group=('Sync', 'Ratings'),
        label='Mode',

        type='enum',
        default=SyncMode.Full,
        options=MODES
    ),

    Property(
        'ratings.conflict',
        group=('Sync', 'Ratings'),
        label='Conflict resolution',

        type='enum',
        default=ConflictResolution.Latest,
        options=CONFLICT_RESOLUTION
    ),

    #
    # Watched
    #

    Property(
        'watched.mode',
        group=('Sync', 'Watched'),
        label='Mode',

        type='enum',
        default=SyncMode.Full,
        options=MODES
    ),
]

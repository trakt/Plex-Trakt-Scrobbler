from plugin.preferences.options.o_backup import *
from plugin.preferences.options.o_sync import *

from plugin.preferences.options.activity import ActivityOption
from plugin.preferences.options.api import ApiOption
from plugin.preferences.options.matcher import MatcherOption
from plugin.preferences.options.pin import PinOption
from plugin.preferences.options.scrobble import ScrobbleOption
from plugin.preferences.options.scrobble_duplication_period import ScrobbleDuplicationPeriodOption

OPTIONS = [
    ActivityOption,
    ApiOption,
    MatcherOption,
    PinOption,

    ScrobbleOption,
    ScrobbleDuplicationPeriodOption,

    # Backup
    BackupMaintenanceIntervalOption,

    # Sync
    SyncActionOption,
    SyncProfilerOption,

    SyncCollectionOption,
    SyncCleanCollectionOption,

    SyncIdleDeferOption,
    SyncIdleDelayOption,

    SyncIntervalOption,
    SyncLibraryUpdateOption,

    SyncPlaybackOption,

    SyncRatingsOption,
    SyncRatingsConflictOption,

    SyncWatchedOption,

    # Sync - Lists
    SyncListsLikedOption,
    SyncListsLikedPlaylistsOption,

    SyncListsPersonalOption,
    SyncListsPersonalPlaylistsOption,

    SyncListsWatchlistOption,
    SyncListsWatchlistPlaylistsOption
]

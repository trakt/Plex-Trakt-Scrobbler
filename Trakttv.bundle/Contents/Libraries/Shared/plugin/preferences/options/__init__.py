from plugin.preferences.options.o_sync import *

from plugin.preferences.options.activity import ActivityOption
from plugin.preferences.options.api import ApiOption
from plugin.preferences.options.matcher import MatcherOption
from plugin.preferences.options.pin import PinOption
from plugin.preferences.options.scrobble import ScrobbleOption

OPTIONS = [
    ActivityOption,
    ApiOption,
    MatcherOption,
    PinOption,
    ScrobbleOption,

    # Sync
    SyncActionOption,
    SyncProfilerOption,

    SyncCollectionOption,
    SyncCleanCollectionOption,

    SyncIntervalOption,
    SyncLibraryUpdateOption,

    SyncPlaybackOption,

    SyncRatingsOption,
    SyncRatingsConflictOption,

    SyncWatchedOption
]

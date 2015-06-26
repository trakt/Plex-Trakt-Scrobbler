from plugin.preferences.options.o_sync import *

from plugin.preferences.options.activity import Activity
from plugin.preferences.options.matcher import Matcher
from plugin.preferences.options.pin import Pin
from plugin.preferences.options.scrobble import Scrobble

OPTIONS = [
    Activity,
    Matcher,
    Pin,
    Scrobble,

    # Sync
    SyncActionModeOption,

    SyncCollection,
    SyncCleanCollection,

    SyncPlayback,

    SyncRatings,
    SyncRatingsConflict,

    SyncWatched
]

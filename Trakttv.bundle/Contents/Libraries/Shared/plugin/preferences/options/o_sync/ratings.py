from plugin.preferences.options.o_sync.constants import PLEX_MODES, PLEX_CONFLICT_RESOLUTION
from plugin.preferences.options.o_sync.core.base import SyncOption

import logging

log = logging.getLogger(__name__)


class SyncRatings(SyncOption):
    __database__ = 'ratings.mode'
    __plex__ = 'sync_ratings'

    def on_plex_changed(self, value):
        if value not in PLEX_MODES:
            log.warn('Unknown value: %r', value)
            return

        # Update database
        self.property.update(
            account=1,
            value=PLEX_MODES[value]
        )


class SyncRatingsConflict(SyncOption):
    __database__ = 'ratings.conflict'
    __plex__ = 'sync_ratings_conflict'

    def on_plex_changed(self, value):
        if value not in PLEX_CONFLICT_RESOLUTION:
            log.warn('Unknown value: %r', value)
            return

        # Update database
        self.property.update(
            account=1,
            value=PLEX_CONFLICT_RESOLUTION[value]
        )

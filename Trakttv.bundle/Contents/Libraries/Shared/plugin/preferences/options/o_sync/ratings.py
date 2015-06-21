from plugin.preferences.options.core.base import Option
from plugin.preferences.options.o_sync.constants import MODES_BY_LABEL, CONFLICT_RESOLUTION_BY_LABEL, MODES_BY_KEY, \
    CONFLICT_RESOLUTION_BY_KEY, ConflictResolution
from plugin.sync.core.enums import SyncMode

import logging

log = logging.getLogger(__name__)


class SyncRatings(Option):
    key = 'sync.ratings.mode'
    type = 'enum'

    choices = MODES_BY_KEY
    default = SyncMode.Full

    group = ('Sync', 'Ratings')
    label = 'Mode'

    preference = 'sync_ratings'

    def on_plex_changed(self, value, account=None):
        if value not in MODES_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MODES_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value


class SyncRatingsConflict(Option):
    key = 'sync.ratings.conflict'
    type = 'enum'

    choices = CONFLICT_RESOLUTION_BY_KEY
    default = ConflictResolution.Latest

    group = ('Sync', 'Ratings')
    label = 'Conflict resolution'

    preference = 'sync_ratings_conflict'

    def on_plex_changed(self, value, account=None):
        if value not in CONFLICT_RESOLUTION_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = CONFLICT_RESOLUTION_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

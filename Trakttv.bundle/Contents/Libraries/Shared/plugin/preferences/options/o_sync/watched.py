from plugin.preferences.options.o_sync.core.base import SyncOption
from plugin.preferences.options.o_sync.constants import PLEX_MODES

import logging

log = logging.getLogger(__name__)


class SyncWatched(SyncOption):
    __database__ = 'watched.mode'
    __plex__ = 'sync_watched'

    def on_plex_changed(self, value):
        if value not in PLEX_MODES:
            log.warn('Unknown value: %r', value)
            return

        # Update database
        self.property.update(
            account=1,
            value=PLEX_MODES[value]
        )

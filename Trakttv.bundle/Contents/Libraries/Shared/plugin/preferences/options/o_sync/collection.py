from plugin.preferences.options.o_sync.constants import PLEX_MODES
from plugin.preferences.options.o_sync.core.base import SyncOption

import logging

log = logging.getLogger(__name__)


class SyncCollection(SyncOption):
    __database__ = 'collection.mode'
    __plex__ = 'sync_collection'

    def on_plex_changed(self, value):
        if value not in PLEX_MODES:
            log.warn('Unknown value: %r', value)
            return

        # Update database
        self.property.update(
            account=1,
            value=PLEX_MODES[value]
        )


class SyncCleanCollection(SyncOption):
    __database__ = 'collection.clean'
    __plex__ = 'sync_clean_collection'

    def on_plex_changed(self, value):
        # Update database
        self.property.update(
            account=1,
            value=value
        )

from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import MODE_KEYS_BY_LABEL, MODE_LABELS_BY_KEY, MODE_IDS_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncCollectionOption(SimpleOption):
    key = 'sync.collection.mode'
    type = 'enum'

    choices = MODE_LABELS_BY_KEY
    default = None

    group = ('Sync', 'Collection')
    label = 'Mode'

    preference = 'sync_collection'

    def on_database_changed(self, value, account=None):
        if value not in MODE_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = MODE_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in MODE_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MODE_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value


class SyncCleanCollectionOption(SimpleOption):
    key = 'sync.collection.clean'
    type = 'boolean'

    default = False

    group = ('Sync', 'Collection')
    label = 'Clean collection'

    preference = 'sync_clean_collection'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

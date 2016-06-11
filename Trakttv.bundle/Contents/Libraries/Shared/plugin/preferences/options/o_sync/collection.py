from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import MODE_KEYS_BY_LABEL, MODE_LABELS_BY_KEY, MODE_IDS_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncCollectionOption(SimpleOption):
    key = 'sync.collection.mode'
    type = 'enum'

    choices = MODE_LABELS_BY_KEY
    default = None

    group = (_('Sync'), _('Collection'))
    label = _('Mode')
    description = _(
        "Defines the syncing mode to use for collected media\n"
        "\n"
        " - **Full** - Synchronize collected media with your Trakt.tv profile (imports changes since your last sync, "
        "then pushes any changes found in Plex)\n"
        " - **Pull** - Import collected media from your Trakt.tv profile\n"
        " - **Push** - Export collected media to your Trakt.tv profile"
    )
    order = 230

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

    group = (_('Sync'), _('Collection'))
    label = _('Clean collection')
    order = 231

    preference = 'sync_clean_collection'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

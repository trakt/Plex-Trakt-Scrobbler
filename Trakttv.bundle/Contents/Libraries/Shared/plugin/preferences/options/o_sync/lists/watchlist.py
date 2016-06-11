from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import MODE_KEYS_BY_LABEL, MODE_LABELS_BY_KEY, MODE_IDS_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncListsWatchlistOption(SimpleOption):
    key = 'sync.lists.watchlist.mode'
    type = 'enum'

    choices = MODE_LABELS_BY_KEY
    default = None

    group = (_('Sync - Lists (Beta)'), _('Watchlist'))
    label = _('Mode')
    description = _(
        "Syncing mode for watchlist items *(applies to both automatic and manual syncs)*.\n"
        "\n"
        " - **Full** - Synchronize watchlist items with your Trakt.tv profile\n"
        " - **Pull** - Only pull watchlist items from your Trakt.tv profile\n"
        " - **Push** - *Not implemented yet*\n"
        " - **Fast Pull** - Only pull changes to watchlist items from your Trakt.tv profile\n"
        " - **Disabled** - Completely disable syncing of watchlist items"
    )
    order = 320

    preference = 'sync_watchlist'

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


class SyncListsWatchlistPlaylistsOption(SimpleOption):
    key = 'sync.lists.watchlist.playlists'
    type = 'boolean'

    default = True

    group = (_('Sync - Lists (Beta)'), _('Watchlist'))
    label = _('Create playlist in plex')
    description = _(
        "Create playlist in Plex if it doesn't already exist."
    )
    order = 321

    # preference = 'sync_watched'
    #
    # def on_database_changed(self, value, account=None):
    #     if value not in MODE_IDS_BY_KEY:
    #         log.warn('Unknown value: %r', value)
    #         return
    #
    #     # Map `value` to plex preference
    #     value = MODE_IDS_BY_KEY[value]
    #
    #     # Update preference
    #     return self._update_preference(value, account)
    #
    # def on_plex_changed(self, value, account=None):
    #     if value not in MODE_KEYS_BY_LABEL:
    #         log.warn('Unknown value: %r', value)
    #         return
    #
    #     # Map plex `value`
    #     value = MODE_KEYS_BY_LABEL[value]
    #
    #     # Update database
    #     self.update(value, account, emit=False)
    #     return value

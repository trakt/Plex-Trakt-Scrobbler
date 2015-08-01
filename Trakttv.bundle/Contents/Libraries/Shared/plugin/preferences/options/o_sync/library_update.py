from plugin.preferences.options.core.base import SimpleOption

import logging

log = logging.getLogger(__name__)


class SyncLibraryUpdateOption(SimpleOption):
    key = 'sync.library_update'
    type = 'boolean'

    default = False

    group = ('Sync', 'Triggers')
    label = 'After library updates'

    preference = 'sync_run_library'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption

import logging

log = logging.getLogger(__name__)


class SyncLibraryUpdateOption(SimpleOption):
    key = 'sync.library_update'
    type = 'boolean'

    default = False

    group = (_('Sync'), _('Triggers'))
    label = _('After library updates')
    description = _(
        "Automatically trigger a \"Full\" sync after your Plex libraries are updated."
    )
    order = 251

    preference = 'sync_run_library'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

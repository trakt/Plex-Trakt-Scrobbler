from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption


class SyncIdleDeferOption(SimpleOption):
    key = 'sync.idle_defer'
    type = 'boolean'

    default = True
    scope = 'server'

    group = (_('Advanced'), _('Sync - Triggers'))
    label = _('Defer until server is idle')
    description = _(
        "Defer automatic syncs until the server isn't streaming any media."
    )
    order = 130

    preference = 'sync_idle_defer'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption

import logging

log = logging.getLogger(__name__)


class ScrobbleOption(SimpleOption):
    key = 'scrobble.enabled'
    type = 'boolean'

    default = True

    group = (_('Scrobble'),)
    label = _('Enabled')
    order = 100

    preference = 'start_scrobble'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

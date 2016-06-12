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
    description = _(
        "Send your watching activity to Trakt.tv in real-time - this will update the \"currently watching\" status on "
        "your profile and mark items as watched when they reach 80% progress."
    )
    order = 100

    preference = 'start_scrobble'

    def on_database_changed(self, value, account=None):
        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

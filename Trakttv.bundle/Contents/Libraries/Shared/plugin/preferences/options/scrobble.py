from plugin.preferences.options.core.base import Option

import logging

log = logging.getLogger(__name__)


class Scrobble(Option):
    key = 'scrobble.enabled'
    type = 'boolean'

    default = True

    group = ('Scrobble',)
    label = 'Enabled'

    preference = 'start_scrobble'

    def on_plex_changed(self, value, account=None):
        # Update database
        self.update(value, account, emit=False)
        return value

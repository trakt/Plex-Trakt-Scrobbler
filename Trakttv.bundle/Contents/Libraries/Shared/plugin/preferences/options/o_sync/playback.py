from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import MODE_KEYS_BY_LABEL, MODE_LABELS_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncPlaybackOption(SimpleOption):
    key = 'sync.playback.mode'
    type = 'enum'

    choices = MODE_LABELS_BY_KEY
    default = None

    group = ('Sync', 'Playback')
    label = 'Mode'
    order = 220

    preference = 'sync_playback'

    def on_plex_changed(self, value, account=None):
        if value not in MODE_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MODE_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

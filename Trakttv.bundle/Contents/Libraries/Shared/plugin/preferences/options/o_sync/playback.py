from plugin.preferences.options.core.base import Option
from plugin.preferences.options.o_sync.constants import MODES_BY_LABEL, MODES_BY_KEY
from plugin.sync.core.enums import SyncMode

import logging

log = logging.getLogger(__name__)


class SyncPlayback(Option):
    key = 'sync.playback.mode'
    type = 'enum'

    choices = MODES_BY_KEY
    default = None

    group = ('Sync', 'Playback')
    label = 'Mode'

    # preference = 'sync_playback'

    @classmethod
    def on_plex_changed(cls, value, account=None):
        if value not in MODES_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Update database
        cls.update(MODES_BY_LABEL[value], account)

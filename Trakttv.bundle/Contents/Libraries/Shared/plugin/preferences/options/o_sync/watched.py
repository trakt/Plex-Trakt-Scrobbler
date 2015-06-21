from plugin.preferences.options.core.base import Option
from plugin.preferences.options.o_sync.constants import MODES_BY_LABEL, MODES_BY_KEY
from plugin.sync.core.enums import SyncMode

import logging

log = logging.getLogger(__name__)


class SyncWatched(Option):
    key = 'sync.watched.mode'
    type = 'enum'

    choices = MODES_BY_KEY
    default = SyncMode.Full

    group = ('Sync', 'Watched')
    label = 'Mode'

    preference = 'sync_watched'

    @classmethod
    def on_plex_changed(cls, value, account=None):
        if value not in MODES_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MODES_BY_LABEL[value]

        # Update database
        cls.update(value, account)
        return value

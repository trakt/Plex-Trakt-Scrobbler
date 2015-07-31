from plugin.preferences.options.core.base import SchedulerOption
from plugin.preferences.options.o_sync.constants import INTERVAL_IDS_BY_KEY, INTERVAL_KEYS_BY_LABEL

import logging

log = logging.getLogger(__name__)


class SyncIntervalOption(SchedulerOption):
    key = 'sync.interval'
    type = 'enum'

    choices = INTERVAL_IDS_BY_KEY
    default = None

    group = ('Sync', 'Triggers')
    label = 'Interval'

    preference = 'sync_run_interval'

    def on_plex_changed(self, value, account=None):
        if value not in INTERVAL_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = INTERVAL_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

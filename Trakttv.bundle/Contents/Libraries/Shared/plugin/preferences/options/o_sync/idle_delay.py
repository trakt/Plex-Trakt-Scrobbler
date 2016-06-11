from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import IDLE_DELAY_LABELS_BY_KEY, IDLE_DELAY_IDS_BY_KEY, \
    IDLE_DELAY_KEYS_BY_LABEL
from plugin.sync.core.enums import SyncIdleDelay

import logging


log = logging.getLogger(__name__)


class SyncIdleDelayOption(SimpleOption):
    key = 'sync.idle_delay'
    type = 'enum'

    choices = IDLE_DELAY_LABELS_BY_KEY
    default = SyncIdleDelay.M30
    scope = 'server'

    group = (_('Advanced'), _('Sync - Triggers'))
    label = _('Idle delay')
    description = _(
        "Wait time before the server is considered idle after media stops being streamed."
    )
    order = 131

    preference = 'sync_idle_delay'

    def on_database_changed(self, value, account=None):
        if value not in IDLE_DELAY_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = IDLE_DELAY_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in IDLE_DELAY_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = IDLE_DELAY_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

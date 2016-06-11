from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.o_sync.constants import DUPLICATION_PERIOD_LABELS_BY_KEY, DUPLICATION_PERIOD_IDS_BY_KEY, \
    DUPLICATION_PERIOD_KEYS_BY_LABEL
from plugin.sync.core.enums import ScrobbleDuplicationPeriod

import logging


log = logging.getLogger(__name__)


class ScrobbleDuplicationPeriodOption(SimpleOption):
    key = 'scrobble.duplication_period'
    type = 'enum'

    choices = DUPLICATION_PERIOD_LABELS_BY_KEY
    default = ScrobbleDuplicationPeriod.H6
    scope = 'server'

    group = (_('Advanced'), _('Scrobble'))
    label = _('Ignore duplicates for')
    description = _(
        "Duplicate scrobbles for a movie or episode are ignored for the defined period.\n"
        "\n"
        "This can help reduce the chances of unintended history duplication if you resume watching something that "
        "has already reached 80% progress (so has already been scrobbled)."
    )
    order = 115

    preference = 'scrobble_duplication_period'

    def on_database_changed(self, value, account=None):
        if value not in DUPLICATION_PERIOD_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = DUPLICATION_PERIOD_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in DUPLICATION_PERIOD_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = DUPLICATION_PERIOD_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

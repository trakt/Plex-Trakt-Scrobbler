from plugin.core.environment import translate as _
from plugin.preferences.options.constants import ACTIVITY_LABELS_BY_KEY, ActivityMode, ACTIVITY_KEYS_BY_LABEL, \
    ACTIVITY_IDS_BY_KEY
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.core.description import Description

import logging

log = logging.getLogger(__name__)


class ActivityOption(SimpleOption):
    key = 'activity.mode'
    type = 'enum'

    choices = ACTIVITY_LABELS_BY_KEY
    default = ActivityMode.Automatic
    scope = 'server'

    group = (_('Advanced'), _('Activity'))
    label = _('Method')
    description = Description(
        _("Method used to retrieve watching activity"), [
            (_("Automatic"), _(
                "Automatically determine available activity method"
            )),
            (_("WebSocket"), _(
                "Retrieve watching activity from the Plex notification channel"
            )),
            (_("Logging"), _(
                "Parse \"Plex Media Server.log\" for watching activity *(higher CPU + Disk IO usage, may block system sleep)*"
            ))
        ]
    )
    order = 100

    preference = 'activity_mode'

    def on_database_changed(self, value, account=None):
        if value not in ACTIVITY_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = ACTIVITY_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in ACTIVITY_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = ACTIVITY_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, emit=False)
        return value

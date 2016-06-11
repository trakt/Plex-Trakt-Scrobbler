from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.core.description import Description
from plugin.preferences.options.o_sync.constants import MODE_KEYS_BY_LABEL, MODE_LABELS_BY_KEY, MODE_IDS_BY_KEY

import logging

log = logging.getLogger(__name__)


class SyncPlaybackOption(SimpleOption):
    key = 'sync.playback.mode'
    type = 'enum'

    choices = MODE_LABELS_BY_KEY
    default = None

    group = (_('Sync'), _('Playback Progress'))
    label = _('Mode')
    description = Description(
        _("Syncing mode for movie and episode playback progress *(applies to both automatic and manual syncs)*."), [
            (_("Full"), _(
                "Synchronize playback progress with your Trakt.tv profile"
            )),
            (_("Pull"), _(
                "Only pull playback progress from your Trakt.tv profile"
            )),
            (_("Push"), _(
                "Only push playback progress to your Trakt.tv profile"
            )),
            (_("Fast Pull"), _(
                "Only pull changes to playback progress from your Trakt.tv profile"
            )),
            (_("Disabled"), _(
                "Completely disable syncing of playback progress"
            )),
        ]
    )
    order = 220

    preference = 'sync_playback'

    def on_database_changed(self, value, account=None):
        if value not in MODE_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = MODE_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in MODE_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MODE_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

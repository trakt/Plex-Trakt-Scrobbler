from plugin.core.environment import translate as _
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.core.description import Description
from plugin.preferences.options.o_sync.constants import MODE_KEYS_BY_LABEL, RESOLUTION_KEYS_BY_LABEL, MODE_LABELS_BY_KEY, \
    RESOLUTION_LABELS_BY_KEY, MODE_IDS_BY_KEY, RESOLUTION_IDS_BY_KEY
from plugin.sync.core.enums import SyncConflictResolution, SyncMode

import logging

log = logging.getLogger(__name__)


class SyncRatingsOption(SimpleOption):
    key = 'sync.ratings.mode'
    type = 'enum'

    choices = MODE_LABELS_BY_KEY
    default = SyncMode.Full

    group = (_('Sync'), _('Ratings'))
    label = _('Mode')
    description = Description(
        _("Syncing mode for movie and episode ratings *(applies to both automatic and manual syncs)*."), [
            (_("Full"), _(
                "Synchronize ratings with your Trakt.tv profile"
            )),
            (_("Pull"), _(
                "Only pull ratings from your Trakt.tv profile"
            )),
            (_("Push"), _(
                "Only push ratings to your Trakt.tv profile"
            )),
            (_("Fast Pull"), _(
                "Only pull changes to ratings from your Trakt.tv profile"
            )),
            (_("Disabled"), _(
                "Completely disable syncing of ratings"
            )),
        ]
    )
    order = 210

    preference = 'sync_ratings'

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


class SyncRatingsConflictOption(SimpleOption):
    key = 'sync.ratings.conflict'
    type = 'enum'

    choices = RESOLUTION_LABELS_BY_KEY
    default = SyncConflictResolution.Latest

    group = (_('Sync'), _('Ratings'))
    label = _('Conflict resolution')
    description = Description(
        _("Rating to use when a conflict exists between Plex and your Trakt.tv profile."), [
            (_("Latest"), _(
                "Use the most recent rating"
            )),
            (_("Trakt"), _(
                "Use the rating from your Trakt.tv profile"
            )),
            (_("Plex"), _(
                "Use the rating from Plex"
            ))
        ]
    )
    order = 211

    preference = 'sync_ratings_conflict'

    def on_database_changed(self, value, account=None):
        if value not in RESOLUTION_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = RESOLUTION_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in RESOLUTION_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = RESOLUTION_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, account, emit=False)
        return value

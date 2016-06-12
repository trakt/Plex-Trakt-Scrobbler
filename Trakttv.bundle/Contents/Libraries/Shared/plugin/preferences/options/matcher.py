from plugin.core.environment import translate as _
from plugin.preferences.options.constants import MATCHER_LABELS_BY_KEY, MatcherMode, MATCHER_KEYS_BY_LABEL, \
    MATCHER_IDS_BY_KEY
from plugin.preferences.options.core.base import SimpleOption
from plugin.preferences.options.core.description import Description

import logging
import plex_metadata

log = logging.getLogger(__name__)


class MatcherOption(SimpleOption):
    key = 'matcher.mode'
    type = 'enum'

    choices = MATCHER_LABELS_BY_KEY
    default = MatcherMode.PlexExtended
    scope = 'server'

    group = (_('Advanced'), _('Matcher'))
    label = _('Mode')
    description = Description(
        _("Matcher to use for episode identification."), [
            (_("Plex"), _(
                "Use the episode identifier provided by Plex"
            )),
            (_("Plex Extended"), _(
                "Use [Caper](https://github.com/fuzeman/caper) to parse episode filenames for an "
                "identifier *(provides better support for multi-episode files)*"
            ))
        ]
    )
    order = 110

    preference = 'matcher'

    def on_changed(self, value, account=None):
        # Update matcher configuration
        extended = value == MatcherMode.PlexExtended

        plex_metadata.Matcher.caper_enabled = extended
        plex_metadata.Matcher.extend_enabled = extended

        log.debug('Configured matcher, extended: %r', extended)

    def on_database_changed(self, value, account=None):
        if value not in MATCHER_IDS_BY_KEY:
            log.warn('Unknown value: %r', value)
            return

        # Map `value` to plex preference
        value = MATCHER_IDS_BY_KEY[value]

        # Update preference
        return self._update_preference(value, account)

    def on_plex_changed(self, value, account=None):
        if value not in MATCHER_KEYS_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MATCHER_KEYS_BY_LABEL[value]

        # Update database
        self.update(value, emit=False)
        return value

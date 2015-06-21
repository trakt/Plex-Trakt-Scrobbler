from plugin.preferences.options.constants import MATCHER_BY_KEY, MatcherMode, MATCHER_BY_LABEL
from plugin.preferences.options.core.base import Option

import logging
import plex_metadata

log = logging.getLogger(__name__)


class Matcher(Option):
    key = 'matcher.mode'
    type = 'enum'

    choices = MATCHER_BY_KEY
    default = MatcherMode.PlexExtended
    scope = 'server'

    group = ('Matcher',)
    label = 'Mode'

    preference = 'matcher'

    def on_changed(self, value, account=None):
        # Update matcher configuration
        extended = value == MatcherMode.PlexExtended

        plex_metadata.Matcher.configure(
            caper_enabled=extended,
            extend_enabled=extended
        )

        log.debug('Configured matcher, extended: %r', extended)

    def on_plex_changed(self, value, account=None):
        if value not in MATCHER_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = MATCHER_BY_LABEL[value]

        # Update database
        self.update(value, emit=False)
        return value

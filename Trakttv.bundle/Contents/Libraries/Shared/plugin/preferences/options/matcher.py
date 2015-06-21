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

    @classmethod
    def on_changed(cls, value, account=None):
        # Update matcher configuration
        extended = value == MatcherMode.PlexExtended

        plex_metadata.Matcher.configure(
            caper_enabled=extended,
            extend_enabled=extended
        )

        log.debug('Configured matcher, extended: %r', extended)

    @classmethod
    def on_plex_changed(cls, value, account=None):
        if value not in MATCHER_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Update database
        cls.update(MATCHER_BY_LABEL[value])

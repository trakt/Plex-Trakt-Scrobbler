from plugin.preferences.options.constants import MATCHER_BY_KEY, MatcherMode, MATCHER_BY_LABEL
from plugin.preferences.options.core.base import Option

import logging

log = logging.getLogger(__name__)


class Scrobble(Option):
    key = 'scrobble.enabled'
    type = 'boolean'

    default = True

    group = ('Scrobble',)
    label = 'Enabled'

    preference = 'start_scrobble'

    @classmethod
    def on_plex_changed(cls, value, account=None):
        # Update database
        cls.update(value, account)

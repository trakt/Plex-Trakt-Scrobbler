from plugin.preferences.options.constants import MATCHER_BY_KEY, MatcherMode, MATCHER_BY_LABEL, ACTIVITY_BY_KEY, \
    ActivityMode, ACTIVITY_BY_LABEL
from plugin.preferences.options.core.base import Option

import logging

log = logging.getLogger(__name__)


class Activity(Option):
    key = 'activity.mode'
    type = 'enum'

    choices = ACTIVITY_BY_KEY
    default = ActivityMode.Automatic
    scope = 'server'

    group = ('Activity',)
    label = 'Mode'

    preference = 'activity_mode'

    @classmethod
    def on_plex_changed(cls, value, account=None):
        if value not in ACTIVITY_BY_LABEL:
            log.warn('Unknown value: %r', value)
            return

        # Map plex `value`
        value = ACTIVITY_BY_LABEL[value]

        # Update database
        cls.update(value)
        return value

from plugin.preferences.options import OPTIONS

import logging

log = logging.getLogger(__name__)

# Construct options
OPTIONS = [o() for o in OPTIONS]

# Build option maps
OPTIONS_BY_KEY = dict([
    (o.key, o)
    for o in OPTIONS
    if o.key
])

OPTIONS_BY_PREFERENCE = dict([
    (o.preference, o)
    for o in OPTIONS
    if o.preference
])


class Preferences(object):
    @classmethod
    def initialize(cls, account=None):
        for option in OPTIONS_BY_KEY.values():
            option.get(account)

    @classmethod
    def on_database_changed(cls, key, value, account=None):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_KEY:
            raise ValueError('Unknown option %r', key)

        option = OPTIONS_BY_KEY[key]

        try:
            option.on_database_changed(value, account=account)
        except Exception:
            log.warn('Unable to process database preference change for %r', key, exc_info=True)

    @classmethod
    def on_plex_changed(cls, key, value, account=None):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_PREFERENCE:
            raise ValueError('Unknown option %r', key)

        option = OPTIONS_BY_PREFERENCE[key]

        try:
            option.on_plex_changed(value, account=account)
        except Exception:
            log.warn('Unable to process plex preference change for %r', key, exc_info=True)

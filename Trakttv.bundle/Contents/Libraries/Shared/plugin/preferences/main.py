from plugin.preferences.options import OPTIONS

import logging

log = logging.getLogger(__name__)

# Construct options
OPTIONS = [o() for o in OPTIONS]

# Build option maps
OPTIONS_BY_DKEY = dict([
    (o.__database__, o)
    for o in OPTIONS
])

OPTIONS_BY_PKEY = dict([
    (o.__plex__, o)
    for o in OPTIONS
])


class Preferences(object):
    @classmethod
    def on_database_changed(cls, key, value):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_DKEY:
            raise ValueError('Unknown option %r', key)

        option = OPTIONS_BY_DKEY[key]

        try:
            option.on_database_changed(value)
        except Exception:
            log.warn('Unable to process database preference change for %r', key, exc_info=True)

    @classmethod
    def on_plex_changed(cls, key, value):
        if not key:
            raise ValueError('Invalid value provided for "pkey"')

        if key not in OPTIONS_BY_PKEY:
            raise ValueError('Unknown option %r', key)

        option = OPTIONS_BY_PKEY[key]

        try:
            option.on_plex_changed(value)
        except Exception:
            log.warn('Unable to process plex preference change for %r', key, exc_info=True)

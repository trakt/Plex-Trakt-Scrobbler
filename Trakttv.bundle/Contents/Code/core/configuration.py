from core.helpers import try_convert
from core.logger import Logger


log = Logger('core.configuration')

MATCHER_MAP = {
    'Plex': 'plex',
    'Plex Extended': 'plex_extended'
}


class ConfigurationProcessor(object):
    def __init__(self):
        self.preferences = None

    def run(self, preferences):
        self.preferences = preferences

        for key in Configuration.keys:
            value = Prefs[Configuration.keys_map.get(key, key)]

            # Transform value if method is available
            if hasattr(self, key):
                value = getattr(self, key)(value)

            if value is not None:
                preferences[key] = value
            else:
                preferences[key] = Configuration.defaults.get(key)
                log.warn('Invalid value specified for option "%s", using default value: %s', key, preferences[key])

    def matcher(self, value):
        return MATCHER_MAP.get(value)

    def scrobble(self, value):
        return value and self.preferences['valid']

    def scrobble_percentage(self, value):
        value = try_convert(value, int)

        if value is None:
            return None

        if 0 <= value <= 100:
            return value

        return None

    def sync_run_library(self, value):
        return value and self.preferences['valid']


class Configuration(object):
    keys = [
        'activity_mode',
        'matcher',
        'scrobble',
        'scrobble_percentage',
        'sync_run_library'
    ]

    keys_map = {
        'scrobble': 'start_scrobble'
    }

    defaults = {
        'scrobble_percentage': 80
    }

    processor = ConfigurationProcessor()

    @classmethod
    def process(cls, preferences):
        cls.processor.run(preferences)

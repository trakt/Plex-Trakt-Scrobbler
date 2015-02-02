from core.helpers import try_convert
from core.logger import Logger


log = Logger('core.configuration')

MATCHER_MAP = {
    'Plex':             'plex',
    'Plex Extended':    'plex_extended'
}

SYNC_TASK_MAP = {
    'Disabled':                     [],
    'Synchronize (Pull + Push)':    ['pull', 'push'],
    'Pull':                         ['pull'],
    'Push':                         ['push']
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

    def sync_run_library(self, value):
        return value and self.preferences['valid']

    def sync_collection(self, value):
        return SYNC_TASK_MAP.get(value)

    def sync_ratings(self, value):
        return SYNC_TASK_MAP.get(value)

    def sync_watched(self, value):
        return SYNC_TASK_MAP.get(value)


class Configuration(object):
    keys = [
        'activity_mode',
        'matcher',
        'scrobble',
        'sync_run_library',
        'sync_collection',
        'sync_ratings',
        'sync_watched'
    ]

    keys_map = {
        'scrobble': 'start_scrobble'
    }

    defaults = {
    }

    processor = ConfigurationProcessor()

    @classmethod
    def process(cls, preferences):
        cls.processor.run(preferences)

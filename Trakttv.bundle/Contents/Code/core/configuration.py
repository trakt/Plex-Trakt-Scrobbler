from core.helpers import try_convert
from core.logger import Logger


log = Logger('core.configuration')


class ConfigurationTransformer(object):
    def run(self, preferences):
        log.debug('ConfigurationTransformer: %s', preferences)

        for key in Configuration.defaults:
            if not hasattr(self, key):
                continue

            value = getattr(self, key)(Prefs[key])

            if value is not None:
                preferences[key] = value
            else:
                preferences[key] = Configuration.defaults[key]
                log.warn('Invalid value specified for option "%s", using default value: %s', key, preferences[key])

    def scrobble_percentage(self, value):
        value = try_convert(value, int)

        if value is None:
            return None

        if 0 <= value <= 100:
            return value

        return None


class Configuration(object):
    defaults = {
        'scrobble_percentage': 80
    }

    transformer = ConfigurationTransformer()

    @classmethod
    def transform(cls, preferences):
        cls.transformer.run(preferences)

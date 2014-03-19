from core.helpers import try_convert
from core.logger import Logger
from plex.plex_base import PlexBase

log = Logger('plex.plex_preferences')


class PlexPreferences(PlexBase):
    @classmethod
    def set(cls, key, value, value_type=None):
        result = cls.request(':/prefs?%s=%s' % (key, try_convert(value, value_type)), 'text', method='PUT')
        if result is None:
            return False

        return True

    @classmethod
    def get(cls, key, value_type=None):
        result = cls.request(':/prefs')
        if result is None:
            return None

        for setting in result.xpath('//Setting'):
            if setting.get('id') == key:
                return cls.convert_value(setting.get('value'), value_type)

        log.warn('Unable to find setting "%s"', key)
        return None

    @classmethod
    def convert_value(cls, value, value_type):
        if not value_type or value_type is str:
            return value

        if value_type is bool:
            return value.lower() == 'true'

        log.warn('Unsupported value type %s', value_type)
        return None

    @classmethod
    def log_debug(cls, value=None):
        if value is None:
            return cls.get('logDebug', bool)

        return cls.set('logDebug', value, int)

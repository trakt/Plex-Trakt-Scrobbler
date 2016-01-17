from logging import Filter
import logging

log = logging.getLogger(__name__)

KEYS = [
    'access_token',
    'refresh_token',

    'token',
    'token_plex',
    'token_server',

    'password'
]

LOGGERS = [
    'trakt.core.emitter',
    'plugin.api.core.manager',
    'plugin.managers.core.base'
]

NOTICE = '[*** sensitive ***]'


class AuthorizationFilter(Filter):
    def filter(self, record):
        if self.is_authorization_message(record):
            return False

        return True

    @classmethod
    def is_authorization_message(cls, record):
        if record.name == 'plugin.core.logger.filters.authorization':
            return False

        if record.name not in LOGGERS:
            return False

        if type(record.args) is not tuple:
            return False

        # Search and replace any arguments containing an authorization fragment
        record.args = tuple(cls.sanitize_arguments(record.args))

        return False

    @classmethod
    def sanitize_arguments(cls, args):
        for value in args:
            if type(value) is str:
                yield cls.sanitize_string(value)
            elif type(value) is dict:
                yield dict(cls.sanitize_dictionary(value))
            else:
                yield value

    @classmethod
    def sanitize_dictionary(cls, d):
        for key, value in list(d.items()):
            if type(value) is dict:
                # Sanitize dictionary
                yield key, dict(cls.sanitize_dictionary(value))
            elif key in KEYS:
                # Sanitize value
                yield key, NOTICE
            else:
                yield key, value

    @classmethod
    def sanitize_string(cls, value):
        if not any([f in value for f in KEYS]):
            return value

        return NOTICE

from plugin.core.environment import Environment
from plugin.preferences.options import OPTIONS

from exception_wrappers import DisabledError
import logging

log = logging.getLogger(__name__)


class Preferences(object):
    @classmethod
    def initialize(cls, account=None):
        scope = 'account' if account is not None else 'server'

        # Initialize preferences
        for key, option in OPTIONS_BY_KEY.items():
            if option.scope != scope:
                continue

            try:
                option.get(account)
            except DisabledError:
                return
            except Exception as ex:
                log.warn('Unable to initialize option %r: %s', key, ex, exc_info=True)

    @classmethod
    def get(cls, key, account=None):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_KEY:
            raise ValueError('Unknown option: %r' % key)

        # Retrieve option from database
        option_cls = OPTIONS_BY_KEY[key]

        try:
            option = option_cls.get(account)
        except DisabledError:
            return option_cls.default
        except Exception as ex:
            log.warn('Unable to retrieve option %r: %s', key, ex, exc_info=True)
            return option_cls.default

        # Return option value
        return option.value

    @classmethod
    def migrate(cls, account=None):
        scope = 'account' if account is not None else 'server'

        # Migrate preferences to database
        for key, option in OPTIONS_BY_PREFERENCE.items():
            if option.scope == scope:
                success = Preferences.on_plex_changed(key, Environment.prefs[key], account=account)
            elif option.scope == scope:
                success = Preferences.on_plex_changed(key, Environment.prefs[key])
            else:
                continue

            if success:
                log.debug('Updated %r option in database', key)

    @classmethod
    def update(cls, key, value, account=None):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_KEY:
            raise ValueError('Unknown option: %r' % key)

        # Update option in database
        option = OPTIONS_BY_KEY[key]
        option.update(value, account)

    #
    # Event handlers
    #

    @classmethod
    def on_database_changed(cls, key, value, account=None):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_KEY:
            raise ValueError('Unknown option: %r' % key)

        option = OPTIONS_BY_KEY[key]

        try:
            value = option.on_database_changed(value, account=account)

            option.on_changed(value, account=account)
            return True
        except Exception:
            log.warn('Unable to process database preference change for %r', key, exc_info=True)

        return False

    @classmethod
    def on_plex_changed(cls, key, value, account=None):
        if not key:
            raise ValueError('Invalid value provided for "key"')

        if key not in OPTIONS_BY_PREFERENCE:
            raise ValueError('Unknown option: %r' % key)

        option = OPTIONS_BY_PREFERENCE[key]

        try:
            value = option.on_plex_changed(value, account=account)

            option.on_changed(value, account=account)
            return True
        except Exception:
            log.warn('Unable to process plex preference change for %r', key, exc_info=True)

        return False


# Construct options
OPTIONS = [o(Preferences) for o in OPTIONS]

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

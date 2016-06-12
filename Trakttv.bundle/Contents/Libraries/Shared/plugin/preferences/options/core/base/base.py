from plugin.core.constants import PLUGIN_IDENTIFIER
from plugin.models import Account
from plugin.preferences.options.core.description import Description

from plex import Plex
import logging

log = logging.getLogger(__name__)


class Option(object):
    key = None
    type = None

    choices = None  # enum
    default = None
    scope = 'account'

    # Display
    group = None
    label = None
    description = None
    order = 0

    # Plex
    preference = None

    def __init__(self, preferences, option=None):
        # Validate class
        if not self.group or not self.label:
            raise ValueError('Missing "group" or "label" attribute on %r', self.__class__)

        if not self.type:
            raise ValueError('Missing "type" attribute on %r', self.__class__)

        if self.type == 'enum' and self.choices is None:
            raise ValueError('Missing enum "choices" attribute on %r', self.__class__)

        if self.scope not in ['account', 'server']:
            raise ValueError('Unknown value for scope: %r', self.scope)

        # Private attributes
        self._option = option
        self._preferences = preferences

        self._value = None

    @property
    def value(self):
        raise NotImplementedError

    def get(self, account=None):
        raise NotImplementedError

    def update(self, value, account=None, emit=True):
        raise NotImplementedError

    def on_database_changed(self, value, account=None):
        if self.preference is None:
            return

        log.warn('[%s] on_database_changed() not implemented, option may not be synchronized with plex', self.key)

    def on_plex_changed(self, value, account=None):
        raise NotImplementedError

    def on_changed(self, value, account=None):
        pass

    def to_dict(self):
        if not self.description:
            log.warn('No description defined for the %r option' % self.key, extra={
                'event': {
                    'module': __name__,
                    'name': 'to_dict.no_description',
                    'key': self.key
                }
            })

        # Ensure descriptions have been built
        if self.description and isinstance(self.description, Description):
            self.description = self.description.build()

        # Build dictionary
        data = {
            'key':      self.key,
            'type':     self.type,

            'default':  self.default,

            'group':    self.group,
            'label':    self.label,
            'order':    self.order,
            'description': self.description,

            'value':    self.value
        }

        if self.type == 'enum':
            data['choices'] = self.choices

        return data

    #
    # Private functions
    #

    def _clone(self, *args):
        return self.__class__(self._preferences, *args)

    @classmethod
    def _update_preference(cls, value, account=None):
        if account is not None and account > 1:
            # Ignore change for non-administrator account
            return value

        # Disable preference migration when validated
        with Plex.configuration.headers({'X-Disable-Preference-Migration': '1'}):
            # Update preference
            Plex[':/plugins/%s/prefs' % PLUGIN_IDENTIFIER].set(cls.preference, value)

        return value

    @staticmethod
    def _validate_account(account):
        if type(account) is int and account < 1:
            return False

        if type(account) is Account and account.id < 1:
            return False

        return True

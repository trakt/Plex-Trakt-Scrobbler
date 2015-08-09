from plugin.models import Account


class Option(object):
    key = None
    type = None

    choices = None  # enum
    default = None
    scope = 'account'

    # Display
    group = None
    label = None
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
        pass

    def on_plex_changed(self, value, account=None):
        raise NotImplementedError

    def on_changed(self, value, account=None):
        pass

    def to_dict(self):
        data = {
            'key':      self.key,
            'type':     self.type,

            'default':  self.default,

            'group':    self.group,
            'label':    self.label,
            'order':    self.order,

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

    @staticmethod
    def _validate_account(account):
        if type(account) is int and account < 1:
            return False

        if type(account) is Account and account.id < 1:
            return False

        return True

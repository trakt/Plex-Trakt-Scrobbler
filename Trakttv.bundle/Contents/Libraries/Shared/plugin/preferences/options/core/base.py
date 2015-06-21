from plugin.models import ConfigurationOption, Account

import msgpack

TYPE_MAP = {
    'boolean':  ('bool',),
    'enum':     ('int',),
    'integer':  ('int',),
    'string':   ('str', 'unicode')
}


class Option(object):
    key = None
    type = None

    choices = None  # enum
    default = None
    scope = 'account'

    # Display
    group = None
    label = None

    # Plex
    preference = None

    def __init__(self, option=None):
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
        self._value = None

    @property
    def value(self):
        if self._option is None:
            return None

        if self._value is None:
            # Unpack value from database
            self._value = self._unpack(self._option.value)

        return self._value

    def get(self, account=None):
        if self.scope == 'account':
            if account is None:
                raise ValueError('Account option requires the "account" parameter')

            if not self._validate_account(account):
                raise ValueError('Invalid value for "account" parameter: %r' % account)

        if self.scope == 'server' and account is not None:
            raise ValueError("Server option can't be called with the \"account\" parameter")

        # Load option from database
        option = ConfigurationOption.get_or_create(
            account=account or 0,
            key=self.key,

            defaults={
                'value': self._pack(self.default),
            }
        )

        return self._clone(option)

    @classmethod
    def on_database_changed(cls, value, account=None):
        raise NotImplementedError

    @classmethod
    def on_plex_changed(cls, value, account=None):
        raise NotImplementedError

    @classmethod
    def on_changed(cls, value, account=None):
        pass

    @classmethod
    def update(cls, value, account=None):
        if cls.scope == 'account':
            if account is None:
                raise ValueError('Account option requires the "account" parameter')

            if not cls._validate_account(account):
                raise ValueError('Invalid value for "account" parameter: %r' % account)

        if cls.scope == 'server' and account is not None:
            raise ValueError("Server option can't be called with the \"account\" parameter")

        ConfigurationOption.insert(
            account=account or 0,
            key=cls.key,

            value=cls._pack(value)
        ).upsert(
            upsert=True
        ).execute()

    #
    # Private functions
    #

    @staticmethod
    def _validate_account(account):
        if type(account) is int and account < 1:
            return False

        if type(account) is Account and account.id < 1:
            return False

        return True

    @classmethod
    def _clone(cls, option):
        return cls(option)

    @classmethod
    def _pack(cls, value):
        value_type = type(value).__name__
        supported = cls._types()

        if value_type not in supported and value_type != 'NoneType':
            raise ValueError("{%s] Value %r doesn't match supported property types: %r" % (cls.key, value, supported))

        if supported == 'enum' and value not in cls.choices:
            raise ValueError("[%s] Value %r doesn't match valid property options: %r" % (cls.key, value, cls.choices.keys()))

        return msgpack.packb(value)

    @staticmethod
    def _unpack(value):
        return msgpack.unpackb(value)

    @classmethod
    def _types(cls):
        try:
            return TYPE_MAP[cls.type]
        except KeyError, ex:
            raise ValueError('Unsupported type: %r' % (cls.type, ))

from plugin.models import ConfigurationOption
from plugin.preferences.options.core.base.base import Option

import logging
import msgpack

log = logging.getLogger(__name__)

TYPE_MAP = {
    'boolean':  ('bool',),
    'enum':     ('int',),
    'integer':  ('int',),
    'string':   ('str', 'unicode')
}


class SimpleOption(Option):
    @property
    def value(self):
        if self._option is None:
            log.warn('Tried to retrieve value from an option without "get()"')
            return None

        if self._value is None:
            # Unpack value from database
            self._value = self._unpack(self._option.value)

        return self._value

    def get(self, account=None):
        # Verify get() call is valid
        if self.scope == 'account':
            if account is None:
                raise ValueError('Account option requires the "account" parameter')

            if not self._validate_account(account):
                raise ValueError('Invalid value for "account" parameter: %r' % account)

        if self.scope == 'server' and account is not None:
            raise ValueError("Server option can't be called with the \"account\" parameter")

        # Load option from database
        option, _ = ConfigurationOption.get_or_create(
            account=account or 0,
            key=self.key,

            defaults={
                'value': self._pack(self.default),
            }
        )

        return self._clone(option)

    def update(self, value, account=None, emit=True):
        if self.scope == 'account':
            if account is None:
                raise ValueError('Account option requires the "account" parameter')

            if not self._validate_account(account):
                raise ValueError('Invalid value for "account" parameter: %r' % account)

        if self.scope == 'server' and account is not None:
            raise ValueError("Server option can't be called with the \"account\" parameter")

        ConfigurationOption.insert(
            account=account or 0,
            key=self.key,

            value=self._pack(value)
        ).upsert(
            upsert=True
        ).execute()

        # Emit database change to handler (if enabled)
        if emit:
            self._preferences.on_database_changed(self.key, value, account=account)

    #
    # Private functions
    #

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
        except KeyError:
            raise ValueError('Unsupported type: %r' % (cls.type, ))

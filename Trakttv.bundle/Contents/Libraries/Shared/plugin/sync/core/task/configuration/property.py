from plugin.models import SyncConfigurationOption

import msgpack

TYPE_MAP = {
    'boolean':  ('bool',),
    'enum':     ('int',),
    'integer':  ('int',),
    'string':   ('str', 'unicode')
}


class Property(object):
    def __init__(self, key, group, label, type='string', default=None, options=None):
        self.key = key

        self.group = group
        self.label = label

        # Meta
        self.type = type
        self.default = default
        self.options = options

        # Retrieve type from map
        try:
            self._type = TYPE_MAP[type]
        except KeyError:
            raise ValueError('Unsupported type: %r', type)

        self._option = None
        self._value = None

    @property
    def value(self):
        if self._option is None:
            return None

        if self._value is None:
            # Unpack value from database
            self._value = self._unpack(self._option.value)

        return self._value

    def get(self, account):
        prop = self._clone()

        # Load option from database
        prop._option, _ = SyncConfigurationOption.get_or_create(
            account=account,
            key=self.key,

            defaults={
                'value': self._pack(self.default),
            }
        )

        return prop

    def _clone(self):
        return Property(
            key=self.key,

            group=self.group,
            label=self.label,

            # Meta
            type=self.type,
            default=self.default,
            options=self.options
        )

    def _pack(self, value):
        value_type = type(value).__name__

        if value_type not in self._type and value_type != 'NoneType':
            raise ValueError("{%s] Value %r doesn't match supported property types: %r" % (self.key, value, self._type))

        if self.type == 'enum' and value not in self.options:
            raise ValueError("[%s] Value %r doesn't match valid property options: %r" % (self.key, value, self.options.keys()))

        return msgpack.packb(value)

    @staticmethod
    def _unpack(value):
        return msgpack.unpackb(value)

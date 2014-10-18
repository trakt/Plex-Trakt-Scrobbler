from plex.objects.core.base import Descriptor, Property


class Setting(Descriptor):
    id = Property

    label = Property
    summary = Property

    type = Property
    group = Property

    value = Property(resolver=lambda: Setting.parse_value)
    default = Property(resolver=lambda: Setting.parse_default)
    options = Property('enumValues', resolver=lambda: Setting.parse_options)

    hidden = Property(type=[int, bool])
    advanced = Property(type=[int, bool])

    @staticmethod
    def parse_value(client, node):
        type = node.get('type')
        value = node.get('value')

        return ['value'], Setting.convert(type, value)

    @staticmethod
    def parse_default(client, node):
        type = node.get('type')
        default = node.get('default')

        return ['default'], Setting.convert(type, default)

    @staticmethod
    def parse_options(client, node):
        value = node.get('enumValues')

        if not value:
            return [], None

        return ['enumValues'], [
            tuple(option.split(':', 2)) for option in value.split('|')
        ]

    @staticmethod
    def convert(type, value):
        if type == 'bool':
            value = value.lower()
            value = value == 'true'
        elif type == 'int':
            value = int(value)

        return value

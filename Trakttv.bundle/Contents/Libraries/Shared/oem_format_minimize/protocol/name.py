from oem_format_minimize.core.minimize import MinimizeProtocol


class NameMinimizeProtocol(MinimizeProtocol):
    __root__ = True
    __ignore__ = True

    __process__ = {
        'item': {
            'optional': True
        }
    }

from oem_format_minimize.core.minimize import MinimizeProtocol
from oem_format_minimize.protocol.metadata import MetadataMinimizeProtocol


class IndexMinimizeProtocol(MinimizeProtocol):
    __root__    = True
    __version__ = 0x01

    items       = 0x01

    MetadataMinimizeProtocol = MetadataMinimizeProtocol.to_child(
        key='items',
        process={
            'children': True
        }
    )

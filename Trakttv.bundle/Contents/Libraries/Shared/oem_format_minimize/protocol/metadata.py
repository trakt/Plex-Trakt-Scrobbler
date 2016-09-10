from oem_format_minimize.core.minimize import MinimizeProtocol


class MetadataMinimizeProtocol(MinimizeProtocol):
    __root__ = True

    hashes      = 0x01
    media       = 0x02

    created_at  = 0x11
    updated_at  = 0x12

    class HashesProtocol(MinimizeProtocol):
        __key__ = 'hashes'
        __ignore__ = True

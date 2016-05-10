from oem_format_minimize.core.minimize import MinimizeProtocol


class MovieMinimizeProtocol(MinimizeProtocol):
    __root__    = True
    __version__ = 0x01

    identifiers     = 0x01
    names           = 0x02

    supplemental    = 0x11
    parameters      = 0x12

    class IdentifiersMinimizeProtocol(MinimizeProtocol):
        __key__ = 'identifiers'

        anidb           = 0x01
        imdb            = 0x02
        tvdb            = 0x03

    class SupplementalMinimizeProtocol(MinimizeProtocol):
        __key__ = 'supplemental'

        studio          = 0x01

    class ParametersMinimizeProtocol(MinimizeProtocol):
        __key__ = 'parameters'

        default_season  = 0x01
        episode_offset  = 0x02

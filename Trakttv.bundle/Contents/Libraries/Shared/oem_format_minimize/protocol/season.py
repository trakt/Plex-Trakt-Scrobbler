from oem_format_minimize.core.minimize import MinimizeProtocol, MinimizeProperty
from oem_format_minimize.protocol.episode import EpisodeMinimizeProtocol
from oem_format_minimize.protocol.name import NameMinimizeProtocol


class SeasonMinimizeProtocol(MinimizeProtocol):
    __root__ = True

    identifiers     = 0x01
    names           = 0x02

    supplemental    = 0x11
    parameters      = 0x12

    mappings        = 0x21

    episodes        = 0x31

    EpisodeMinimizeProtocol = EpisodeMinimizeProtocol.to_child(
        key='episodes',
        process={
            'children': True
        }
    )

    NameMinimizeProtocol = NameMinimizeProtocol.to_child(
        key='names',
        process={
            'children': True
        }
    )

    class IdentifiersMinimizeProtocol(MinimizeProtocol):
        __key__ = 'identifiers'

        anidb           = 0x01
        imdb            = 0x02
        tvdb            = 0x03
        tmdb_movie      = MinimizeProperty('tmdb:movie', 0x04)
        tmdb_show       = MinimizeProperty('tmdb:show',  0x05)

    class SupplementalMinimizeProtocol(MinimizeProtocol):
        __key__ = 'supplemental'

        studio          = 0x01

    class ParametersMinimizeProtocol(MinimizeProtocol):
        __key__ = 'parameters'

        default_season  = 0x01
        episode_offset  = 0x02

    class SeasonMappingMinimizeProtocol(MinimizeProtocol):
        __key__ = 'mappings'

        identifiers = 0x01
        names       = 0x02

        season      = 0x11

        start       = 0x21
        end         = 0x22
        offset      = 0x23

        class IdentifiersMinimizeProtocol(MinimizeProtocol):
            __key__ = 'identifiers'

            anidb           = 0x01
            imdb            = 0x02
            tvdb            = 0x03
            tmdb_movie      = MinimizeProperty('tmdb:movie', 0x04)
            tmdb_show       = MinimizeProperty('tmdb:show',  0x05)

        NameMinimizeProtocol = NameMinimizeProtocol.to_child(
            key='names',
            process={
                'children': True
            }
        )

from plugin.core.environment import translate as _


class Enum(object):
    @classmethod
    def parse(cls, value):
        options = cls.options()

        result = []

        for k, v in options.items():
            if type(v) is not int or v == 0:
                continue

            if value == 0 or (value & v) == v:
                result.append(v)

        return result

    @classmethod
    def options(cls):
        result = {}

        for key in dir(cls):
            if key.startswith('_'):
                continue

            result[key] = getattr(cls, key)

        return result


class SyncActionMode(Enum):
    Update  = 0x00
    Log     = 0x01


class SyncProfilerMode(Enum):
    Disabled    = None
    Basic       = 0x01


class SyncConflictResolution(Enum):
    Latest  = 0x00
    Trakt   = 0x01
    Plex    = 0x02


class SyncData(Enum):
    All             = 0
    Collection      = 1
    Playback        = 2
    Ratings         = 4
    Watched         = 8
    Watchlist       = 16

    # Lists
    Liked           = 32
    Personal        = 64

    __titles__ = None

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            # Build titles map
            cls.__titles__ = {
                cls.All:           _('All'),
                cls.Collection:    _('Collection'),
                cls.Playback:      _('Playback'),
                cls.Ratings:       _('Ratings'),
                cls.Watched:       _('Watched'),
                cls.Watchlist:     _('Watchlist')
            }

        return cls.__titles__.get(value)


class ScrobbleDuplicationPeriod(Enum):
    H1      = 1 * 60
    H3      = 3 * 60
    H6      = 6 * 60
    H12     = 12 * 60

    D1      = 1 * 24 * 60
    D7      = 7 * 24 * 60


class SyncIdleDelay(Enum):
    M15     = 15
    M30     = 30

    H1      = 1 * 60


class SyncInterval(Enum):
    M15     = '*/15 * * * *'
    M30     = '*/30 * * * *'

    H1      = '0 * * * *'
    H3      = '0 */3 * * *'
    H6      = '0 */6 * * *'
    H12     = '0 */12 * * *'

    D1      = '0 0 * * *'
    D7      = '0 0 */7 * *'


class SyncMedia(Enum):
    All         = 0
    Movies      = 1
    Shows       = 2
    Seasons     = 4
    Episodes    = 8
    Lists       = 16

    __titles__ = None

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            # Build titles map
            cls.__titles__ = {
                cls.All:        _('All'),
                cls.Movies:     _('Movies'),
                cls.Shows:      _('Shows'),
                cls.Seasons:    _('Seasons'),
                cls.Episodes:   _('Episodes'),
            }

        return cls.__titles__.get(value)


class SyncMode(Enum):
    Full        = 0x00
    Pull        = 0x01
    Push        = 0x02
    FastPull    = 0x04

    __titles__ = None

    @classmethod
    def title(cls, value):
        if cls.__titles__ is None:
            # Build titles map
            cls.__titles__ = {
                cls.Full:       _('Full'),
                cls.Pull:       _('Pull'),
                cls.Push:       _('Push'),
                cls.FastPull:   _('Quick Pull')
            }

        return cls.__titles__.get(value)

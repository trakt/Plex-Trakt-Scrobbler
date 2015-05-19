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


class Media(Enum):
    All         = 0x00
    Movies      = 0x01
    Shows       = 0x02
    Seasons     = 0x04
    Episodes    = 0x08

    __map__ = None

    @classmethod
    def get(cls, key):
        if cls.__map__ is None:
            cls.__map__ = {
                Media.Movies:     'movies',
                Media.Shows:      'shows',
                Media.Seasons:    'seasons',
                Media.Episodes:   'episodes'
            }

        return cls.__map__.get(key)


class Data(Enum):
    All         = 0x00
    Collection  = 0x01
    Playback    = 0x02
    Ratings     = 0x04
    Watched     = 0x08
    Watchlist   = 0x16

    __attributes__ = None

    @classmethod
    def initialize(cls):
        if cls.__attributes__:
            return

        cls.__attributes__ = {
            Data.Collection: {
                'interface': 'sync/collection',
                'timestamp': 'collected_at'
            },
            Data.Playback: {
                'interface': 'sync/playback',
                'timestamp': 'paused_at'
            },
            Data.Ratings: {
                'interface': 'sync/ratings',
                'timestamp': 'rated_at'
            },
            Data.Watched: {
                'interface': 'sync/watched',
                'timestamp': 'watched_at'
            },
            Data.Watchlist: {
                'interface': 'sync/watchlist',
                'timestamp': 'watchlisted_at'
            }
        }

    @classmethod
    def get_interface(cls, key):
        return cls.get_attribute(key, 'interface')

    @classmethod
    def get_timestamp_key(cls, key):
        return cls.get_attribute(key, 'timestamp')

    @classmethod
    def get_attribute(cls, key, attribute):
        cls.initialize()

        attributes = cls.__attributes__.get(key)

        if not attributes:
            return None

        return attributes.get(attribute)
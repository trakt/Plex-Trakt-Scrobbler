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
    All         = 0
    Movies      = 1
    Shows       = 2
    Seasons     = 4
    Episodes    = 8

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
    All             = 0
    Collection      = 1
    Playback        = 2
    Ratings         = 4
    Watched         = 8
    Watchlist       = 16

    ListLiked       = 32
    ListPersonal    = 64

    __attributes__ = None
    __map__ = None

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
            },

            Data.ListLiked: {
                'interface': 'users/likes',
                'timestamp': 'updated_at'
            },
            Data.ListPersonal: {
                'interface': 'users/*/lists',
                'timestamp': 'updated_at'
            }
        }

    @classmethod
    def get(cls, key):
        if cls.__map__ is None:
            cls.__map__ = {
                Data.Collection:    'collection',
                Data.Playback:      'playback',
                Data.Ratings:       'ratings',
                Data.Watched:       'watched',
                Data.Watchlist:     'watchlist',

                Data.ListLiked:     ('lists', 'liked'),
                Data.ListPersonal:  ('lists', 'personal')
            }

        return cls.__map__.get(key)

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
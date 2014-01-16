from core.helpers import build_repr


class TraktMedia(object):
    def __init__(self, keys=None):
        self.keys = keys

        self.rating = None
        self.rating_advanced = None
        self.rating_timestamp = None

    def update(self, info, keys):
        for key in keys:
            if key not in info:
                continue

            setattr(self, key, info[key])

    def fill(self, info):
        self.update(info, ['rating', 'rating_advanced'])

        if 'rating' in info:
            self.rating_timestamp = info.get('inserted')

    @staticmethod
    def get_repr_keys():
        return ['keys', 'rating', 'rating_advanced', 'rating_timestamp']

    def __repr__(self):
        return build_repr(self, self.get_repr_keys() or [])

    def __str__(self):
        return self.__repr__()


class TraktShow(TraktMedia):
    def __init__(self, keys):
        super(TraktShow, self).__init__(keys)

        self.title = None
        self.year = None
        self.tvdb_id = None

        self.episodes = {}

    def fill(self, info, is_watched=None):
        TraktMedia.fill(self, info)

        self.update(info, ['title', 'year', 'tvdb_id'])

        if 'seasons' in info:
            self.update_seasons(info['seasons'], is_watched)

        return self

    def update_seasons(self, seasons, is_watched=None):
        for season, episodes in [(x.get('season'), x.get('episodes')) for x in seasons]:
            for episode in episodes:
                self.episodes[(season, episode)] = TraktEpisode(season, episode, is_watched)

    @classmethod
    def create(cls, keys, info, is_watched=None):
        show = cls(keys)
        return cls.fill(show, info, is_watched)

    @staticmethod
    def get_repr_keys():
        return TraktMedia.get_repr_keys() + ['title', 'year', 'tvdb_id', 'episodes']


class TraktEpisode(TraktMedia):
    def __init__(self, season, number, is_watched=None):
        super(TraktEpisode, self).__init__()

        self.season = season
        self.number = number

        self.is_watched = is_watched

    @staticmethod
    def get_repr_keys():
        return TraktMedia.get_repr_keys() + ['season', 'number', 'is_watched']


class TraktMovie(TraktMedia):
    def __init__(self, keys):
        super(TraktMovie, self).__init__(keys)

        self.title = None
        self.year = None
        self.imdb_id = None

        self.is_watched = None

    def fill(self, info):
        TraktMedia.fill(self, info)
        self.update(info, ['title', 'year', 'imdb_id'])

        return self

    @classmethod
    def create(cls, keys, info, is_watched=None):
        movie = cls(keys)
        movie.is_watched = is_watched

        return cls.fill(movie, info)

    @staticmethod
    def get_repr_keys():
        return TraktMedia.get_repr_keys() + ['title', 'year', 'imdb_id', 'is_watched']

from core.helpers import build_repr


class TraktMedia(object):
    def __init__(self, keys=None):
        self.keys = keys

        self.rating = None
        self.rating_advanced = None
        self.rating_timestamp = None

        self.is_watched = None
        self.is_collected = None

    def update(self, info, keys):
        for key in keys:
            if key not in info:
                continue

            if getattr(self, key) is not None:
                continue

            setattr(self, key, info[key])

    def update_states(self, is_watched=None, is_collected=None):
        if is_watched is not None:
            self.is_watched = is_watched

        if is_collected is not None:
            self.is_collected = is_collected

    def fill(self, info):
        self.update(info, ['rating', 'rating_advanced'])

        if 'rating' in info:
            self.rating_timestamp = info.get('inserted')

    @staticmethod
    def get_repr_keys():
        return ['keys', 'rating', 'rating_advanced', 'rating_timestamp', 'is_watched', 'is_collected']

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

    def fill(self, info, is_watched=None, is_collected=None):
        TraktMedia.fill(self, info)

        self.update(info, ['title', 'year', 'tvdb_id'])

        if 'seasons' in info:
            self.update_seasons(info['seasons'], is_watched, is_collected)

        return self

    def update_seasons(self, seasons, is_watched=None, is_collected=None):
        for season, episodes in [(x.get('season'), x.get('episodes')) for x in seasons]:
            # For each episode, create if doesn't exist, otherwise just update is_watched and is_collected
            for episode in episodes:
                key = season, episode

                if key not in self.episodes:
                    self.episodes[key] = TraktEpisode.create(season, episode, is_watched, is_collected)
                else:
                    self.episodes[key].update_states(is_watched, is_collected)

    @classmethod
    def create(cls, keys, info, is_watched=None, is_collected=None):
        show = cls(keys)
        return cls.fill(show, info, is_watched, is_collected)

    @staticmethod
    def get_repr_keys():
        return TraktMedia.get_repr_keys() + ['title', 'year', 'tvdb_id', 'episodes']


class TraktEpisode(TraktMedia):
    def __init__(self, season, number):
        super(TraktEpisode, self).__init__()

        self.season = season
        self.number = number

    @classmethod
    def create(cls, season, number, is_watched=None, is_collected=None):
        episode = cls(season, number)
        episode.update_states(is_watched, is_collected)

        return episode

    @staticmethod
    def get_repr_keys():
        return TraktMedia.get_repr_keys() + ['season', 'number']


class TraktMovie(TraktMedia):
    def __init__(self, keys):
        super(TraktMovie, self).__init__(keys)

        self.title = None
        self.year = None
        self.imdb_id = None

    def fill(self, info):
        TraktMedia.fill(self, info)
        self.update(info, ['title', 'year', 'imdb_id'])

        return self

    @classmethod
    def create(cls, keys, info, is_watched=None, is_collected=None):
        movie = cls(keys)
        movie.update_states(is_watched, is_collected)

        return cls.fill(movie, info)

    @staticmethod
    def get_repr_keys():
        return TraktMedia.get_repr_keys() + ['title', 'year', 'imdb_id']

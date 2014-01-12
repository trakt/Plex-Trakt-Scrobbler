from core.helpers import build_repr


class TraktMedia(object):
    def __init__(self):
        self.rating = None
        self.rating_advanced = None

    def update(self, info, **kwargs):
        for key, value in info.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __str__(self):
        return self.__repr__()


class TraktShow(TraktMedia):
    def __init__(self):
        super(TraktShow, self).__init__()

        self.title = None
        self.year = None
        self.tvdb_id = None

        self.episodes = {}

    def update(self, info, is_watched=None):
        for key, value in info.items():
            if key == 'seasons':
                self.update_seasons(value, is_watched)
            elif hasattr(self, key):
                setattr(self, key, value)

    def update_seasons(self, seasons, is_watched=None):
        for season, episodes in [(x.get('season'), x.get('episodes')) for x in seasons]:
            for episode in episodes:
                self.episodes[(season, episode)] = TraktEpisode(season, episode, is_watched)

    @classmethod
    def create(cls, info, is_watched=None):
        show = cls()
        show.update(info, is_watched)

        return show

    def __repr__(self):
        return build_repr(self, ['tvdb_id', 'title', 'year', 'rating', 'rating_advanced', 'episodes'])


class TraktEpisode(TraktMedia):
    def __init__(self, season, number, is_watched=None):
        super(TraktEpisode, self).__init__()

        self.season = season
        self.number = number

        self.is_watched = is_watched

    def __repr__(self):
        return build_repr(self, ['season', 'number', 'is_watched', 'rating', 'rating_advanced'])


class TraktMovie(TraktMedia):
    def __init__(self):
        super(TraktMovie, self).__init__()

        self.title = None
        self.year = None
        self.imdb_id = None

        self.is_watched = None

    @classmethod
    def create(cls, info, is_watched=None):
        movie = cls()
        movie.is_watched = is_watched

        movie.update(info)

        return movie

    def __repr__(self):
        return build_repr(self, ['imdb_id', 'title', 'year', 'is_watched', 'rating', 'rating_advanced'])

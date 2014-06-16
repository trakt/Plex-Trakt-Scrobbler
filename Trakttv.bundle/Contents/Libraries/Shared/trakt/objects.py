from trakt.helpers import update_attributes


class Media(object):
    def __init__(self, keys=None):
        self.keys = keys

        self.rating = None

    @property
    def pk(self):
        if not self.keys:
            return None

        return self.keys[0]

    def update(self, info=None, **kwargs):
        self.rating = Rating.create(info) or self.rating

    def __str__(self):
        return self.__repr__()


class Video(Media):
    def __init__(self, keys=None):
        super(Video, self).__init__(keys)

        self.is_watched = None
        self.is_collected = None

    def update(self, info=None, is_watched=None, is_collected=None):
        super(Video, self).update(info)

        if is_watched is not None:
            self.is_watched = is_watched

        if is_collected is not None:
            self.is_collected = is_collected


class Show(Media):
    def __init__(self, keys):
        super(Show, self).__init__(keys)

        self.title = None
        self.year = None
        self.tvdb_id = None

        self.episodes = {}

    def to_info(self):
        return {
            'tvdb_id': self.tvdb_id,
            'title': self.title,
            'year': self.year
        }

    def update(self, info=None, **kwargs):
        super(Show, self).update(info, **kwargs)

        update_attributes(self, info, ['title', 'year', 'tvdb_id'])

    @classmethod
    def create(cls, keys, info=None, **kwargs):
        show = cls(keys)
        show.update(info, **kwargs)

        return show

    def __repr__(self):
        return '<Show "%s" (%s)>' % (self.title, self.year)


class Episode(Video):
    def __init__(self, pk):
        super(Episode, self).__init__([pk])

    def to_info(self):
        season, episode = self.pk

        return {
            'season': season,
            'episode': episode
        }

    @classmethod
    def create(cls, pk, info=None, **kwargs):
        episode = cls(pk)
        episode.update(info, **kwargs)

        return episode

    def __repr__(self):
        return '<Episode S%02dE%02d>' % self.pk


class Movie(Video):
    def __init__(self, keys):
        super(Movie, self).__init__(keys)

        self.title = None
        self.year = None
        self.imdb_id = None

        self.is_watched = None
        self.is_collected = None

    def to_info(self):
        return {
            'title': self.title,
            'year': self.year,
            'imdb_id': self.imdb_id
        }

    def update(self, info=None, **kwargs):
        super(Movie, self).update(info, **kwargs)

        update_attributes(self, info, ['title', 'year', 'imdb_id'])

    @classmethod
    def create(cls, keys, info, **kwargs):
        movie = cls(keys)
        movie.update(info, **kwargs)

        return movie

    def __repr__(self):
        return '<Movie "%s" (%s)>' % (self.title, self.year)


class Rating(object):
    def __init__(self):
        self.basic = None
        self.advanced = None

        self.timestamp = None

    @classmethod
    def create(cls, info):
        if not info or 'rating' not in info:
            return

        r = cls()
        r.basic = info.get('rating')
        r.advanced = info.get('rating_advanced')

        r.timestamp = info.get('inserted')
        return r

    def __repr__(self):
        return '<Rating %s (%s/10)>' % (self.basic, self.advanced)

    def __str__(self):
        return self.__repr__()

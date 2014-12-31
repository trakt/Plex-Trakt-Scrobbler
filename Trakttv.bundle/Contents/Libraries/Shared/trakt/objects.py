from trakt.core.helpers import to_datetime
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

        self.collected_at = None
        self.plays = None

        self.is_watched = None
        self.is_collected = None

    def update(self, info=None, is_watched=None, is_collected=None):
        super(Video, self).update(info)

        update_attributes(self, info, [
            'plays'
        ])

        self.collected_at = to_datetime(info.get('collected_at'))

        # Set flags
        if is_watched is not None:
            self.is_watched = is_watched

        if is_collected is not None:
            self.is_collected = is_collected


class Show(Media):
    def __init__(self, keys):
        super(Show, self).__init__(keys)

        self.title = None
        self.year = None

        self.seasons = {}

    def episodes(self):
        for sk, season in self.seasons.iteritems():
            # Yield each episode in season
            for ek, episode in season.episodes.iteritems():
                yield (sk, ek), episode

    def to_info(self):
        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    def update(self, info=None, **kwargs):
        super(Show, self).update(info, **kwargs)

        update_attributes(self, info, ['title', 'year'])

    @classmethod
    def create(cls, keys, info=None, **kwargs):
        show = cls(keys)
        show.update(info, **kwargs)

        return show

    def __repr__(self):
        return '<Show %r (%s)>' % (self.title, self.year)


class Season(Media):
    def __init__(self, number):
        super(Season, self).__init__([number])

        self.episodes = {}

    def to_info(self):
        return {
            'number': self.pk,
            'episodes': [
                episode.to_info()
                for episode in self.episodes.values()
            ]
        }

    @classmethod
    def create(cls, number, info=None, **kwargs):
        season = cls(number)
        season.update(info, **kwargs)

        return season

    def __repr__(self):
        return '<Season S%02d>' % self.pk


class Episode(Video):
    def __init__(self, number):
        super(Episode, self).__init__([number])

    def to_info(self):
        return {
            'number': self.pk
        }

    @classmethod
    def create(cls, pk, info=None, **kwargs):
        episode = cls(pk)
        episode.update(info, **kwargs)

        return episode

    def __repr__(self):
        return '<Episode E%02d>' % self.pk


class Movie(Video):
    def __init__(self, keys):
        super(Movie, self).__init__(keys)

        self.title = None
        self.year = None

    def to_info(self):
        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    def update(self, info=None, **kwargs):
        super(Movie, self).update(info, **kwargs)

        update_attributes(self, info['movie'], ['title', 'year'])

    @classmethod
    def create(cls, keys, info, **kwargs):
        movie = cls(keys)
        movie.update(info, **kwargs)

        return movie

    def __repr__(self):
        return '<Movie %r (%s)>' % (self.title, self.year)


class Rating(object):
    def __init__(self):
        self.value = None
        self.timestamp = None

    @classmethod
    def create(cls, info):
        if not info or 'rating' not in info:
            return

        r = cls()
        r.value = info.get('rating')
        r.timestamp = to_datetime(info.get('rated_at'))
        return r

    def __repr__(self):
        return '<Rating %s/10 (%s)>' % (self.value, self.timestamp)

    def __str__(self):
        return self.__repr__()

from trakt.core.helpers import from_iso8601, to_iso8601, deprecated
from trakt.helpers import update_attributes


class Media(object):
    def __init__(self, keys=None):
        self.keys = keys

        self.images = None
        self.overview = None
        self.rating = None
        self.score = None

    @property
    def pk(self):
        if not self.keys:
            return None

        return self.keys[0]

    def update(self, info=None, **kwargs):
        update_attributes(self, info, [
            'overview',
            'images',
            'score'
        ])

        self.rating = Rating.create(info) or self.rating

    def __str__(self):
        return self.__repr__()


class Video(Media):
    def __init__(self, keys=None):
        super(Video, self).__init__(keys)

        self.last_watched_at = None
        self.collected_at = None
        self.paused_at = None

        self.plays = None
        self.progress = None

        self.is_watched = None
        self.is_collected = None

    def update(self, info=None, is_watched=None, is_collected=None):
        super(Video, self).update(info)

        update_attributes(self, info, [
            'plays',
            'progress'
        ])

        if 'last_watched_at' in info:
            self.last_watched_at = from_iso8601(info.get('last_watched_at'))

        if 'collected_at' in info:
            self.collected_at = from_iso8601(info.get('collected_at'))

        if 'paused_at' in info:
            self.paused_at = from_iso8601(info.get('paused_at'))

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

    def to_identifier(self):
        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    @deprecated('Show.to_info() has been moved to Show.to_dict()')
    def to_info(self):
        return self.to_dict()

    def to_dict(self):
        result = self.to_identifier()

        result['seasons'] = [
            season.to_dict()
            for season in self.seasons.values()
        ]

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601(self.rating.timestamp)

        return result

    def update(self, info=None, **kwargs):
        super(Show, self).update(info, **kwargs)

        update_attributes(self, info, ['title'])

        if info.get('year'):
            self.year = int(info['year'])

    @classmethod
    def create(cls, keys, info=None, **kwargs):
        show = cls(keys)
        show.update(info, **kwargs)

        return show

    def __repr__(self):
        return '<Show %r (%s)>' % (self.title, self.year)


class Season(Media):
    def __init__(self, keys=None):
        super(Season, self).__init__(keys)

        self.show = None
        self.episodes = {}

    def to_identifier(self):
        return {
            'number': self.pk,
            'episodes': [
                episode.to_dict()
                for episode in self.episodes.values()
            ]
        }

    @deprecated('Season.to_info() has been moved to Season.to_dict()')
    def to_info(self):
        return self.to_dict()

    def to_dict(self):
        result = self.to_identifier()

        result.update({
            'ids': dict([
                (key, value) for (key, value) in self.keys[1:]  # NOTE: keys[0] is the season identifier
            ])
        })

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601(self.rating.timestamp)

        return result

    @classmethod
    def create(cls, keys, info=None, **kwargs):
        season = cls(keys)
        season.update(info, **kwargs)

        return season

    def __repr__(self):
        return '<Season S%02d>' % self.pk


class Episode(Video):
    def __init__(self, keys=None):
        super(Episode, self).__init__(keys)

        self.show = None
        self.season = None

        self.title = None

    def to_identifier(self):
        _, number = self.pk

        return {
            'number': number
        }

    @deprecated('Episode.to_info() has been moved to Episode.to_dict()')
    def to_info(self):
        return self.to_dict()

    def to_dict(self):
        result = self.to_identifier()

        result.update({
            'title': self.title,

            'watched': 1 if self.is_watched else 0,
            'collected': 1 if self.is_collected else 0,

            'plays': self.plays if self.plays is not None else 0,
            'progress': self.progress,

            'last_watched_at': to_iso8601(self.last_watched_at),
            'collected_at': to_iso8601(self.collected_at),
            'paused_at': to_iso8601(self.paused_at),

            'ids': dict([
                (key, value) for (key, value) in self.keys[1:]  # NOTE: keys[0] is the (<season>, <episode>) identifier
            ])
        })

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601(self.rating.timestamp)

        return result

    def update(self, info=None, **kwargs):
        super(Episode, self).update(info, **kwargs)

        update_attributes(self, info, ['title'])

    @classmethod
    def create(cls, keys, info=None, **kwargs):
        episode = cls(keys)
        episode.update(info, **kwargs)

        return episode

    def __repr__(self):
        if self.title:
            return '<Episode S%02dE%02d - %r>' % (self.pk[0], self.pk[1], self.title)

        return '<Episode S%02dE%02d>' % self.pk


class Movie(Video):
    def __init__(self, keys):
        super(Movie, self).__init__(keys)

        self.title = None
        self.year = None

    def to_identifier(self):
        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    @deprecated('Movie.to_info() has been moved to Movie.to_dict()')
    def to_info(self):
        return self.to_dict()

    def to_dict(self):
        result = self.to_identifier()

        result.update({
            'watched': 1 if self.is_watched else 0,
            'collected': 1 if self.is_collected else 0,

            'plays': self.plays if self.plays is not None else 0,
            'progress': self.progress,

            'last_watched_at': to_iso8601(self.last_watched_at),
            'collected_at': to_iso8601(self.collected_at),
            'paused_at': to_iso8601(self.paused_at)
        })

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601(self.rating.timestamp)

        return result

    def update(self, info=None, **kwargs):
        super(Movie, self).update(info, **kwargs)

        update_attributes(self, info, ['title'])

        if info.get('year'):
            self.year = int(info['year'])

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
        r.timestamp = from_iso8601(info.get('rated_at'))
        return r

    def __repr__(self):
        return '<Rating %s/10 (%s)>' % (self.value, self.timestamp)

    def __str__(self):
        return self.__repr__()

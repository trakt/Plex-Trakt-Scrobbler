from trakt.core.helpers import to_iso8601, deprecated
from trakt.objects.core.helpers import update_attributes
from trakt.objects.video import Video


class Movie(Video):
    def __init__(self, client, keys, index=None):
        super(Movie, self).__init__(client, keys, index)

        self.title = None
        self.year = None

        self.watchers = None  # trending

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
            'in_watchlist': self.in_watchlist if self.in_watchlist is not None else 0,
            'progress': self.progress,

            'last_watched_at': to_iso8601(self.last_watched_at),
            'collected_at': to_iso8601(self.collected_at),
            'paused_at': to_iso8601(self.paused_at)
        })

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601(self.rating.timestamp)

        return result

    def _update(self, info=None, **kwargs):
        super(Movie, self)._update(info, **kwargs)

        update_attributes(self, info, [
            'title',
            'watchers'  # trending
        ])

        if info.get('year'):
            self.year = int(info['year'])

    @classmethod
    def _construct(cls, client, keys, info, index=None, **kwargs):
        movie = cls(client, keys, index=index)
        movie._update(info, **kwargs)

        return movie

    def __repr__(self):
        return '<Movie %r (%s)>' % (self.title, self.year)

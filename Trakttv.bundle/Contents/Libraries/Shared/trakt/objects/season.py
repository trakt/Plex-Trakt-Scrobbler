from trakt.core.helpers import to_iso8601, deprecated
from trakt.objects.media import Media


class Season(Media):
    def __init__(self, client, keys=None, index=None):
        super(Season, self).__init__(client, keys, index)

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

        result['in_watchlist'] = self.in_watchlist if self.in_watchlist is not None else 0

        return result

    @classmethod
    def _construct(cls, client, keys, info=None, index=None, **kwargs):
        season = cls(client, keys, index=index)
        season._update(info, **kwargs)

        return season

    def __repr__(self):
        return '<Season S%02d>' % self.pk

from trakt.core.helpers import to_iso8601, deprecated
from trakt.objects.core.helpers import update_attributes
from trakt.objects.video import Video


class Episode(Video):
    def __init__(self, client, keys=None, index=None):
        super(Episode, self).__init__(client, keys, index)

        self.show = None
        """
        :type: :class:`trakt.objects.show.Show`

        Show
        """

        self.season = None
        """
        :type: :class:`trakt.objects.season.Season`

        Season
        """

        self.title = None
        """
        :type: :class:`~python:str`

        Episode title
        """

    def to_identifier(self):
        """Returns the episode identifier which is compatible with requests that require
        episode definitions.

        :return: Episode identifier/definition
        :rtype: :class:`~python:dict`
        """

        _, number = self.pk

        return {
            'number': number
        }

    @deprecated('Episode.to_info() has been moved to Episode.to_dict()')
    def to_info(self):
        """**Deprecated:** use the :code:`to_dict()` method instead"""
        return self.to_dict()

    def to_dict(self):
        """Dump episode to a dictionary

        :return: Episode dictionary
        :rtype: :class:`~python:dict`
        """

        result = self.to_identifier()

        result.update({
            'title': self.title,

            'watched': 1 if self.is_watched else 0,
            'collected': 1 if self.is_collected else 0,

            'plays': self.plays if self.plays is not None else 0,
            'in_watchlist': self.in_watchlist if self.in_watchlist is not None else 0,
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

    def _update(self, info=None, **kwargs):
        super(Episode, self)._update(info, **kwargs)

        update_attributes(self, info, ['title'])

    @classmethod
    def _construct(cls, client, keys, info=None, index=None, **kwargs):
        episode = cls(client, keys, index=index)
        episode._update(info, **kwargs)

        return episode

    def __repr__(self):
        if self.show and self.title:
            return '<Episode %r - S%02dE%02d - %r>' % (self.show.title, self.pk[0], self.pk[1], self.title)

        if self.show:
            return '<Episode %r - S%02dE%02d>' % (self.show.title, self.pk[0], self.pk[1])

        if self.title:
            return '<Episode S%02dE%02d - %r>' % (self.pk[0], self.pk[1], self.title)

        return '<Episode S%02dE%02d>' % self.pk

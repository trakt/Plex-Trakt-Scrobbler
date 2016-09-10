from trakt.core.helpers import to_iso8601, deprecated
from trakt.objects.core.helpers import update_attributes
from trakt.objects.media import Media

from six import iteritems


class Show(Media):
    def __init__(self, client, keys, index=None):
        super(Show, self).__init__(client, keys, index)

        self.title = None
        """
        :type: :class:`~python:str`

        Show title
        """

        self.year = None
        """
        :type: :class:`~python:int`

        Show year
        """

        self.seasons = {}
        """
        :type: :class:`~python:dict`

        Seasons, defined as :code:`{season_num: Season}`

        **Note:** this field might not be available with some methods
        """

        self.watchers = None
        """
        :type: :class:`~python:int`

        Number of active watchers (returned by the :code:`Trakt['movies'].trending()`
        and :code:`Trakt['shows'].trending()` methods)
        """

    def episodes(self):
        """Returns a flat episode iterator

        :returns: Iterator :code:`((season_num, episode_num), Episode)`
        :rtype: iterator
        """

        for sk, season in iteritems(self.seasons):
            # Yield each episode in season
            for ek, episode in iteritems(season.episodes):
                yield (sk, ek), episode

    def to_identifier(self):
        """Returns the show identifier which is compatible with requests that require
        show definitions.

        :return: Show identifier/definition
        :rtype: :class:`~python:dict`
        """

        return {
            'ids': dict(self.keys),
            'title': self.title,
            'year': self.year
        }

    @deprecated('Show.to_info() has been moved to Show.to_dict()')
    def to_info(self):
        """**Deprecated:** use the :code:`to_dict()` method instead"""
        return self.to_dict()

    def to_dict(self):
        """Dump show to a dictionary

        :return: Show dictionary
        :rtype: :class:`~python:dict`
        """

        result = self.to_identifier()

        result['seasons'] = [
            season.to_dict()
            for season in self.seasons.values()
        ]

        if self.rating:
            result['rating'] = self.rating.value
            result['rated_at'] = to_iso8601(self.rating.timestamp)

        result['in_watchlist'] = self.in_watchlist if self.in_watchlist is not None else 0

        return result

    def _update(self, info=None, **kwargs):
        super(Show, self)._update(info, **kwargs)

        update_attributes(self, info, [
            'title',

            'watchers'  # trending
        ])

        if info.get('year'):
            self.year = int(info['year'])

    @classmethod
    def _construct(cls, client, keys, info=None, index=None, **kwargs):
        show = cls(client, keys, index=index)
        show._update(info, **kwargs)

        return show

    def __repr__(self):
        return '<Show %r (%s)>' % (self.title, self.year)

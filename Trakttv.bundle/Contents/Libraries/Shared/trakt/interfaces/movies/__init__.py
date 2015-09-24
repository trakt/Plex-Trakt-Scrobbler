from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class MoviesInterface(Interface):
    path = 'movies'

    def get(self, id, **kwargs):
        response = self.http.get(
            str(id)
        )

        # Parse response
        return SummaryMapper.movie(
            self.client,
            self.get_data(response, **kwargs)
        )

    def trending(self, **kwargs):
        response = self.http.get(
            'trending'
        )

        return SummaryMapper.movies(
            self.client,
            self.get_data(response, **kwargs)
        )

from trakt.interfaces.base import Interface
from trakt.mapper.summary import SummaryMapper


class MoviesInterface(Interface):
    path = 'movies'

    def get(self, id, extended=None, **kwargs):
        response = self.http.get(str(id), query={
            'extended': extended
        })

        # Parse response
        return SummaryMapper.movie(
            self.client,
            self.get_data(response, **kwargs)
        )

    def trending(self, extended=None, **kwargs):
        response = self.http.get('trending', query={
            'extended': extended
        })

        return SummaryMapper.movies(
            self.client,
            self.get_data(response, **kwargs)
        )

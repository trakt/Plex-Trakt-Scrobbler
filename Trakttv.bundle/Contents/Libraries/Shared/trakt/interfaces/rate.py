from trakt.interfaces.base import Interface, authenticated


class RateInterface(Interface):
    path = 'rate'

    @authenticated
    def movies(self, movies, credentials=None):
        """Rate one or more movies on trakt. If a movie is already rated, the rating will
        be replaced.

        This method will not sent out any social updates. This method can handle quite a
        bit of data input, but we'd recommend sending multiple smaller batches if you
        experience slow response times.

        :param movies: list of movie ratings
        :type movies: list of dict {title, year, rating, [imdb_id], [tmdb_id]}
        """
        return self.action(
            'movies', data={'movies': movies},
            credentials=credentials
        )

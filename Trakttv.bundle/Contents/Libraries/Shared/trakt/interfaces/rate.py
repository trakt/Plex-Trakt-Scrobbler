from trakt.interfaces.base import Interface, authenticated


class RateInterface(Interface):
    path = 'rate'

    @authenticated
    def episodes(self, episodes, **kwargs):
        """Rate one or more episodes on trakt. If an episode is already rated, the rating will
        be replaced.

        This method will not sent out any social updates. This method can handle quite a bit
        of data input, but we'd recommend sending multiple smaller batches if you experience
        slow response times.

        :param episodes: list of episode ratings
        :type episodes: list of dict {title, year, season, episode, rating, [imdb_id], [tvdb_id]}
        """
        return self.action(
            'episodes', {
                'episodes': episodes
            },
            **kwargs
        )

    @authenticated
    def movies(self, movies, **kwargs):
        """Rate one or more movies on trakt. If a movie is already rated, the rating will
        be replaced.

        This method will not sent out any social updates. This method can handle quite a
        bit of data input, but we'd recommend sending multiple smaller batches if you
        experience slow response times.

        :param movies: list of movie ratings
        :type movies: list of dict {title, year, rating, [imdb_id], [tmdb_id]}
        """
        return self.action(
            'movies', {
                'movies': movies
            },
            **kwargs
        )

    @authenticated
    def shows(self, shows, **kwargs):
        """Rate one or more shows on trakt. If a show is already rated, the rating will
        be replaced.

        This method will not sent out any social updates. This method can handle quite a
        bit of data input, but we'd recommend sending multiple smaller batches if you
        experience slow response times.

        :param shows: list of show ratings
        :type shows: list of dict {title, year, rating, [imdb_id], [tvdb_id]}
        """
        return self.action(
            'shows', {
                'shows': shows
            },
            **kwargs
        )

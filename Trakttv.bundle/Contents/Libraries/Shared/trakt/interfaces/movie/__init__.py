from trakt.interfaces.base import authenticated, media_center
from trakt.interfaces.base.media import MediaInterface


class MovieInterface(MediaInterface):
    path = 'movie'

    @media_center
    @authenticated
    def scrobble(self, duration, progress, **kwargs):
        """Notify trakt that a user has finished watching a movie.

        This commits the movie to the users profile. You should use movie/watching
        prior to calling this method.

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int

        :param title: Movie title.
        :type title: str

        :param year: Movie year.
        :type year: int
        """
        return self.action(
            'scrobble', {
                'duration': duration,
                'progress': progress
            },
            **kwargs
        )

    @authenticated
    def seen(self, movies, **kwargs):
        """Add movies watched outside of trakt to your library.

        :param movies: list of movies to mark as seen
        :type movies: list of dict {title, year, [imdb_id], [last_played]}
        """
        return self.action(
            'seen', data={
                'movies': movies
            },
            **kwargs
        )

    @authenticated
    def library(self, movies, **kwargs):
        """Add movies to your library collection.

        :param movies: list of movies to add to your collection
        :type movies: list of dict {title, year, [imdb_id]}
        """
        return self.action(
            'library', data={
                'movies': movies
            },
            **kwargs
        )

    @media_center
    @authenticated
    def watching(self, duration, progress, **kwargs):
        """Notify trakt that a user has started watching a movie.

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int

        :param title: Movie title.
        :type title: str

        :param year: Movie year.
        :type year: int
        """
        return self.action(
            'watching', {
                'duration': duration,
                'progress': progress
            },
            **kwargs
        )

    @authenticated
    def unlibrary(self, movies, **kwargs):
        """Remove movies from your library collection.

        :param movies: list of movies to remove from your collection
        :type movies: list of dict {title, year, [imdb_id]}
        """
        return self.action(
            'unlibrary', data={
                'movies': movies
            },
            **kwargs
        )

    @authenticated
    def unseen(self, movies, **kwargs):
        """Remove episodes watched outside of trakt from your watched history.

        :param movies: list of movies to remove from your watched history
        :type movies: list of dict {title, year, [imdb_id]}
        """
        return self.action(
            'unseen', {
                'movies': movies
            },
            **kwargs
        )

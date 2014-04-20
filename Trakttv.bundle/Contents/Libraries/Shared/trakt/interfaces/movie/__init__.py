from trakt.interfaces.base import authenticated, media_center
from trakt.interfaces.base.media import MediaInterface


class MovieInterface(MediaInterface):
    path = 'movie'

    @media_center
    @authenticated
    def scrobble(self, title, year, duration, progress, credentials=None, **kwargs):
        """Notify trakt that a user has finished watching a movie.

        This commits the movie to the users profile. You should use movie/watching
        prior to calling this method.

        :param title: Movie title.
        :type title: str

        :param year: Movie year.
        :type year: int

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int
        """
        data = {
            'title': title,
            'year': year,

            'duration': duration,
            'progress': progress
        }

        data.update(kwargs)

        return self.action(
            'scrobble', data,
            credentials=credentials
        )

    @authenticated
    def seen(self, movies, credentials=None):
        """Add movies watched outside of trakt to your library.

        :param movies: list of movies to mark as seen
        :type movies: list of dict {title, year, [imdb_id], [last_played]}
        """
        return self.action(
            'seen', data={'movies': movies},
            credentials=credentials
        )

    @authenticated
    def library(self, movies, credentials=None):
        """Add movies to your library collection.

        :param movies: list of movies to add to your collection
        :type movies: list of dict {title, year, [imdb_id]}
        """
        return self.action(
            'library', data={'movies': movies},
            credentials=credentials
        )

    @media_center
    @authenticated
    def watching(self, title, year, duration, progress, credentials=None, **kwargs):
        """Notify trakt that a user has started watching a movie.

        :param title: Movie title.
        :type title: str

        :param year: Movie year.
        :type year: int

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int
        """
        data = {
            'title': title,
            'year': year,

            'duration': duration,
            'progress': progress
        }

        data.update(kwargs)

        return self.action(
            'watching', data,
            credentials=credentials
        )

    @authenticated
    def unlibrary(self, movies, credentials=None):
        """Remove movies from your library collection.

        :param movies: list of movies to remove from your collection
        :type movies: list of dict {title, year, [imdb_id]}
        """
        return self.action(
            'unlibrary', data={'movies': movies},
            credentials=credentials
        )

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

        return self.send(
            'scrobble', data,
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

        return self.send(
            'watching', data,
            credentials=credentials
        )

from trakt.interfaces.base import authenticated, media_center
from trakt.interfaces.base.media import MediaInterface


class ShowInterface(MediaInterface):
    path = 'show'

    @media_center
    @authenticated
    def scrobble(self, title, year, season, episode, duration, progress, credentials=None, **kwargs):
        """Notify trakt that a user has finished watching a show.

        This commits the show to the users profile. You should use show/watching
        prior to calling this method.

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int

        :param season: Show season. Send 0 if watching a special.
        :type season: int

        :param episode: Show episode.
        :type episode: int

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int
        """
        data = {
            'title': title,
            'year': year,

            'season': season,
            'episode': episode,

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
    def watching(self, title, year, season, episode, duration, progress, credentials=None, **kwargs):
        """Notify trakt that a user has started watching a show.

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int

        :param season: Show season. Send 0 if watching a special.
        :type season: int

        :param episode: Show episode.
        :type episode: int

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int
        """
        data = {
            'title': title,
            'year': year,

            'season': season,
            'episode': episode,

            'duration': duration,
            'progress': progress
        }

        data.update(kwargs)

        return self.send(
            'watching', data,
            credentials=credentials
        )

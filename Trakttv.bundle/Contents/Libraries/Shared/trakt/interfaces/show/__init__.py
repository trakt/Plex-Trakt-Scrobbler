from trakt.interfaces.base import authenticated, media_center
from trakt.interfaces.base.media import MediaInterface


class ShowInterface(MediaInterface):
    path = 'show'

    @media_center
    @authenticated
    def scrobble(self, season, episode, duration, progress, **kwargs):
        """Notify trakt that a user has finished watching a show.

        This commits the show to the users profile. You should use show/watching
        prior to calling this method.

        :param season: Show season. Send 0 if watching a special.
        :type season: int

        :param episode: Show episode.
        :type episode: int

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int
        """
        return self.action(
            'scrobble', {
                'season': season,
                'episode': episode,

                'duration': duration,
                'progress': progress
            },
            **kwargs
        )

    @media_center
    @authenticated
    def watching(self, season, episode, duration, progress, **kwargs):
        """Notify trakt that a user has started watching a show.

        :param season: Show season. Send 0 if watching a special.
        :type season: int

        :param episode: Show episode.
        :type episode: int

        :param duration: Duration in minutes.
        :type duration: int

        :param progress: % progress, integer 0-100.
        :type progress: int

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int
        """
        return self.action(
            'watching', {
                'season': season,
                'episode': episode,

                'duration': duration,
                'progress': progress
            },
            **kwargs
        )

    @authenticated
    def unlibrary(self, title=None, year=None, **kwargs):
        """Remove an entire show (including all episodes) from your library collection.

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int
        """
        return self.action(
            'unlibrary', {
                'title': title,
                'year': year
            },
            **kwargs
        )

    @classmethod
    def validate_action(cls, action, data):
        if action in ['unlibrary']:
            if not cls.data_requirements(data, ('title', 'year'), 'imdb_id', 'tvdb_id'):
                return False

        return True

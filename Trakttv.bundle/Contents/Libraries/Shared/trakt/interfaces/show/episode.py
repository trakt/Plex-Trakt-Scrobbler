from trakt.interfaces.base import Interface, authenticated


class ShowEpisodeInterface(Interface):
    path = 'show/episode'

    @authenticated
    def library(self, title, year, episodes, **kwargs):
        """Add episodes to your library collection.

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int

        :param episodes: list of episodes to add to your collection
        :type episodes: list of dict {season, episode}
        """
        return self.action(
            'library', {
                'title': title,
                'year': year,
                'episodes': episodes
            },
            **kwargs
        )

    @authenticated
    def seen(self, title, year, episodes, **kwargs):
        """Add episodes watched outside of trakt to your library.

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int

        :param episodes: list of episodes to add to your collection
        :type episodes: list of dict {season, episode, [last_played]}
        """
        return self.action(
            'seen', {
                'title': title,
                'year': year,
                'episodes': episodes
            },
            **kwargs
        )

    @authenticated
    def unlibrary(self, title, year, episodes, **kwargs):
        """Remove episodes from your library collection.

        :param title: Show title.
        :type title: str

        :param year: Show year.
        :type year: int

        :param episodes: list of episodes to add to your collection
        :type episodes: list of dict {season, episode}
        """
        return self.action(
            'unlibrary', {
                'title': title,
                'year': year,
                'episodes': episodes
            },
            **kwargs
        )

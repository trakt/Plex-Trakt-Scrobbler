from trakt.interfaces.base import Interface, authenticated


class UserRatingsInterface(Interface):
    path = 'user/ratings'

    @authenticated
    def get(self, media, username=None, rating='all', extended=None, store=None, credentials=None):
        # Fill username with currently authenticated user (if nothing is provided)
        if username is None:
            username = credentials.get('username')

        response = self.request(
            '%s.json' % media,
            [username, rating, extended],
            credentials=credentials
        )

        items = self.get_data(response)

        return self.media_mapper(store, media, items)

    @authenticated
    def episodes(self, username=None, rating='all', extended=None, store=None, credentials=None):
        """Returns all episodes a user has rated.

        :param username: User to fetch details on, defaults to authenticated user.
        :type username: str

        :param rating: By default, this assume `all` ratings will be returned. Specify rating
                       to filter by, `love`, `hate` or advanced rating integer.
        :type rating: str or int

        :param extended: By default, this returns the minimal info. Set to `normal` for more
                         info (url, images, genres). Set to full for full info.
        :param extended: str
        """
        return self.get(
            'episodes', username,
            rating, extended,
            store=store,
            credentials=credentials
        )

    @authenticated
    def movies(self, username=None, rating='all', extended=None, store=None, credentials=None):
        """Returns all movies a user has rated.

        :param username: User to fetch details on, defaults to authenticated user.
        :type username: str

        :param rating: By default, this assume `all` ratings will be returned. Specify rating
                       to filter by, `love`, `hate` or advanced rating integer.
        :type rating: str or int

        :param extended: By default, this returns the minimal info. Set to `normal` for more
                         info (url, images, genres). Set to full for full info.
        :param extended: str
        """
        return self.get(
            'movies', username,
            rating, extended,
            store=store,
            credentials=credentials
        )

    @authenticated
    def shows(self, username=None, rating='all', extended=None, store=None, credentials=None):
        """Returns all shows a user has rated.

        :param username: User to fetch details on, defaults to authenticated user.
        :type username: str

        :param rating: By default, this assume `all` ratings will be returned. Specify rating
                       to filter by, `love`, `hate` or advanced rating integer.
        :type rating: str or int

        :param extended: By default, this returns the minimal info. Set to `normal` for more
                         info (url, images, genres). Set to full for full info.
        :param extended: str
        """
        return self.get(
            'shows', username,
            rating, extended,
            store=store,
            credentials=credentials
        )

from trakt.interfaces.base import Interface, authenticated


class UserLibraryInterface(Interface):
    path = 'user/library'

    @authenticated
    def get(self, media, library, username=None, extended=None, store=None, credentials=None):
        # Fill username with currently authenticated user (if nothing is provided)
        if username is None:
            username = credentials.get('username')

        response = self.request(
            '%s/%s.json' % (media, library),
            [username, extended],
            credentials=credentials
        )

        items = self.get_data(response)

        if type(items) is not list:
            return None

        flags = self.get_flags(library)

        return self.media_mapper(store, media, items, **flags)

    @staticmethod
    def get_flags(library):
        if library == 'collection':
            return {'is_collected': True}

        if library == 'watched':
            return {'is_watched': True}

        return {}

    @authenticated
    def all(self, media, username=None, extended=None, store=None, credentials=None):
        """Returns all the items in a user's library.

        Each item will indicate if it's in the user's collection and how many plays
        it has.

        :param username: User to fetch details on, defaults to authenticated user.
        :type username: str

        :param extended: Returns complete movie info if set to `true`. Returns only
                         the minimal info required for media center syncing if set
                         to `min`.
        :param extended: str

        :param store: Existing dictionary to use, allows the merging of multiple data sources.
        :type store: dict
        """
        return self.get(
            media, 'all',
            username, extended,
            store=store,
            credentials=credentials
        )

    @authenticated
    def collection(self, media, username=None, extended=None, store=None, credentials=None):
        """Returns all the items in a user's collection.

        Collection items might include blu-rays, dvds, and digital downloads.

        :param username: User to fetch details on, defaults to authenticated user.
        :type username: str

        :param extended: Returns complete movie info if set to `true`. Returns only
                         the minimal info required for media center syncing if set
                         to `min`.
        :param extended: str

        :param store: Existing dictionary to use, allows the merging of multiple data sources.
        :type store: dict
        """
        return self.get(
            media, 'collection',
            username, extended,
            store=store,
            credentials=credentials
        )

    @authenticated
    def watched(self, media, username=None, extended=None, store=None, credentials=None):
        """Returns all items that a user has watched.

        This method is useful to sync trakt's data with local media center.

        :param username: User to fetch details on, defaults to authenticated user.
        :type username: str

        :param extended: Returns complete movie info if set to `true`. Returns only
                         the minimal info required for media center syncing if set
                         to `min`.
        :param extended: str

        :param store: Existing dictionary to use, allows the merging of multiple data sources.
        :type store: dict
        """
        return self.get(
            media, 'watched',
            username, extended,
            store=store,
            credentials=credentials
        )

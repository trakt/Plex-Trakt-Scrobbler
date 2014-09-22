from trakt.interfaces.base import Interface, authenticated


class SyncBaseInterface(Interface):
    flags = {}

    @authenticated
    def get(self, media, store=None, params=None):
        r_params = [media]

        if params:
            r_params.extend(params)

        response = self.http.get(
            params=r_params
        )

        items = self.get_data(response)

        if type(items) is not list:
            return None

        return self.media_mapper(
            store, media, items,
            **self.flags
        )

    @authenticated
    def post(self, data):
        response = self.http.post(
            data=data
        )

        data = self.get_data(response)

        if not data:
            return False

        return data

    @authenticated
    def delete(self, data):
        pass

    #
    # Shortcut methods
    #

    @authenticated
    def shows(self, store=None):
        return self.get(
            'shows',
            store
        )

    @authenticated
    def movies(self, store=None):
        return self.get(
            'movies',
            store
        )

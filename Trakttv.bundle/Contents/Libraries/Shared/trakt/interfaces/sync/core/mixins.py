from trakt.interfaces.base import authenticated, Interface


class Get(Interface):
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


class Add(Interface):
    @authenticated
    def add(self, items):
        response = self.http.post(
            data=items
        )

        return self.get_data(response)


class Remove(Interface):
    @authenticated
    def remove(self, items):
        response = self.http.post(
            'remove',
            data=items
        )

        return self.get_data(response)

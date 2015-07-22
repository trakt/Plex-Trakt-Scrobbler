from trakt.interfaces.base import authenticated, Interface
from trakt.mapper.sync import SyncMapper


class Get(Interface):
    flags = {}

    @authenticated
    def get(self, media, store=None, params=None, **kwargs):
        r_params = [media]

        if params:
            r_params.extend(params)

        response = self.http.get(
            params=r_params,

            authenticated=kwargs.pop('authenticated', None)
        )

        items = self.get_data(response, **kwargs)

        if type(items) is not list:
            return None

        return SyncMapper.process(
            self.client, store, items, media,
            **self.flags
        )

    @authenticated
    def shows(self, store=None, **kwargs):
        return self.get(
            'shows',
            store,
            **kwargs
        )

    @authenticated
    def movies(self, store=None, **kwargs):
        return self.get(
            'movies',
            store,
            **kwargs
        )


class Add(Interface):
    @authenticated
    def add(self, items, **kwargs):
        response = self.http.post(
            data=items,

            authenticated=kwargs.pop('authenticated', None)
        )

        return self.get_data(response, **kwargs)


class Remove(Interface):
    @authenticated
    def remove(self, items, **kwargs):
        response = self.http.post(
            'remove',
            data=items,

            authenticated=kwargs.pop('authenticated', None)
        )

        return self.get_data(response, **kwargs)

from trakt.core.pagination import PaginationIterator
from trakt.interfaces.base import authenticated, Interface
from trakt.mapper.sync import SyncMapper


class Get(Interface):
    flags = {}

    @authenticated
    def get(self, media=None, store=None, params=None, query=None, flat=False, **kwargs):
        if not params:
            params = []

        params.insert(0, media)

        # Request resource
        response = self.http.get(
            params=params,
            query=query,

            authenticated=kwargs.pop('authenticated', None)
        )

        # Parse response
        items = self.get_data(response, **kwargs)

        if type(items) is not list and not isinstance(items, PaginationIterator):
            return None

        # Map items
        return SyncMapper.process(
            self.client, store, items,
            media=media,
            flat=flat,
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

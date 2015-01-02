from trakt.interfaces.base import authenticated
from trakt.interfaces.sync.core.mixins import Get, Add, Remove


class SyncRatingsInterface(Get, Add, Remove):
    path = 'sync/ratings'

    @authenticated
    def get(self, media, store=None, rating=None):
        parameters = []

        if rating is not None:
            parameters.append(rating)

        return super(SyncRatingsInterface, self).get(media, store, parameters)

    #
    # Shortcut methods
    #

    @authenticated
    def shows(self, store=None, rating=None):
        return self.get('shows', store, rating,)

    @authenticated
    def seasons(self, store=None, rating=None):
        return self.get('seasons', store, rating,)

    @authenticated
    def episodes(self, store=None, rating=None):
        return self.get('episodes', store, rating)

    @authenticated
    def movies(self, store=None, rating=None):
        return self.get('movies', store, rating)

from trakt.core.helpers import from_iso8601
from trakt.objects.core.helpers import update_attributes
from trakt.objects.rating import Rating


class Media(object):
    def __init__(self, client, keys=None, index=None):
        self._client = client

        self.keys = keys
        self.index = index

        self.images = None
        self.overview = None
        self.rating = None
        self.score = None

        # Flags
        self.in_watchlist = None

        # Timestamps
        self.listed_at = None

    @property
    def pk(self):
        if not self.keys:
            return None

        return self.keys[0]

    def _update(self, info=None, in_watchlist=None, **kwargs):
        if not info:
            return

        update_attributes(self, info, [
            'overview',
            'score'
        ])

        if 'images' in info:
            self.images = info['images']

        # Set timestamps
        if 'listed_at' in info:
            self.listed_at = from_iso8601(info.get('listed_at'))

        # Set flags
        if in_watchlist is not None:
            self.in_watchlist = in_watchlist

        self.rating = Rating._construct(self._client, info) or self.rating

    def __getstate__(self):
        state = self.__dict__

        if hasattr(self, '_client'):
            del state['_client']

        return state

    def __str__(self):
        return self.__repr__()
